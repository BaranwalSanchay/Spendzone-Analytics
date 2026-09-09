"""Concurrent load test against a real running uvicorn server (asyncio + httpx, no
external load-testing service) for /api/upload and /api/budget-scenario. Reports
p50/p95/p99 latency and throughput at a stated concurrency level.

This script starts its own uvicorn subprocess on a dedicated port and tears it down
when done, so the whole thing is one reproducible command -- no separate "start the
server first" step.

Run (from Spendzone-Analytics/, using system Python -- backend's deps):
    python scripts/metrics/load_test.py
"""
import asyncio
import os
import platform
import statistics
import subprocess
import sys
import time

import httpx

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
SAMPLE_CSV = os.path.join(REPO_ROOT, "scripts", "sample_data", "sample_marketing_spend.csv")

PORT = 8765
BASE_URL = f"http://127.0.0.1:{PORT}"
CONCURRENCY = 10
N_REQUESTS = 60  # per endpoint


async def wait_for_server(client: httpx.AsyncClient, timeout=20.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = await client.get(f"{BASE_URL}/api/health", timeout=1.0)
            if resp.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        await asyncio.sleep(0.3)
    raise RuntimeError("Server did not become healthy in time")


async def run_upload_requests(client: httpx.AsyncClient, csv_bytes: bytes):
    sem = asyncio.Semaphore(CONCURRENCY)
    latencies = []

    async def one():
        async with sem:
            start = time.perf_counter()
            resp = await client.post(
                f"{BASE_URL}/api/upload",
                files={"file": ("sample.csv", csv_bytes, "text/csv")},
            )
            latencies.append(time.perf_counter() - start)
            assert resp.status_code == 200, resp.text

    wall_start = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(N_REQUESTS)))
    wall_elapsed = time.perf_counter() - wall_start
    return latencies, wall_elapsed


async def run_budget_scenario_requests(client: httpx.AsyncClient):
    sem = asyncio.Semaphore(CONCURRENCY)
    latencies = []

    async def one():
        async with sem:
            start = time.perf_counter()
            resp = await client.post(f"{BASE_URL}/api/budget-scenario", json={"total_budget": 100000})
            latencies.append(time.perf_counter() - start)
            assert resp.status_code == 200, resp.text

    wall_start = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(N_REQUESTS)))
    wall_elapsed = time.perf_counter() - wall_start
    return latencies, wall_elapsed


def percentile(values, p):
    values = sorted(values)
    idx = min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))
    return values[idx]


def report(label, latencies, wall_elapsed):
    p50 = percentile(latencies, 50) * 1000
    p95 = percentile(latencies, 95) * 1000
    p99 = percentile(latencies, 99) * 1000
    throughput = len(latencies) / wall_elapsed
    print(f"\n{label} (n={len(latencies)}, concurrency={CONCURRENCY}):")
    print(f"  p50={p50:.1f}ms  p95={p95:.1f}ms  p99={p99:.1f}ms  throughput={throughput:.1f} req/s")


async def main():
    print(f"Hardware: {platform.platform()}, {platform.processor() or 'unknown CPU'}, "
          f"{os.cpu_count()} logical cores")
    print(f"Concurrency: {CONCURRENCY}, requests per endpoint: {N_REQUESTS}")

    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--port", str(PORT)],
        cwd=BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        async with httpx.AsyncClient() as client:
            await wait_for_server(client)

            with open(SAMPLE_CSV, "rb") as f:
                csv_bytes = f.read()

            upload_latencies, upload_wall = await run_upload_requests(client, csv_bytes)
            report("/api/upload", upload_latencies, upload_wall)

            scenario_latencies, scenario_wall = await run_budget_scenario_requests(client)
            report("/api/budget-scenario", scenario_latencies, scenario_wall)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    asyncio.run(main())
