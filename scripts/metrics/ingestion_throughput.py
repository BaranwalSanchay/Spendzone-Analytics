"""Time /api/upload end to end (parse + schema validation + profiling) across CSVs of
increasing size, using scripts/generate_sample_data.py's own long-format generator to
build each size rather than a separate synthetic dataset.

Uses FastAPI's TestClient (in-process ASGI calls, no real socket) so timing isolates the
endpoint's own processing cost from OS-level network variance -- this measures parse +
validation + profiling, which is what the claim is about, not network latency (that's
covered separately by scripts/metrics/load_test.py against a real running server).

Run (from Spendzone-Analytics/, using system Python -- backend's deps, not ds-pipeline's):
    python scripts/metrics/ingestion_throughput.py
"""
import io
import os
import sys
import time

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, SCRIPTS_DIR)

os.chdir(BACKEND_DIR)  # api.py's file-based paths (plots/, data/) are relative to backend/
from fastapi.testclient import TestClient  # noqa: E402
import api  # noqa: E402
from generate_sample_data import generate_long_format_spend, RANDOM_SEED  # noqa: E402

DAY_SIZES = [30, 90, 365, 1000, 3000]  # days of daily spend across 7 channels each
REPEATS = 5  # per size, report the median to reduce noise from the first-call warmup


def main():
    client = TestClient(api.app)

    print(f"{'Days':>6}{'Rows':>10}{'Median Time (s)':>18}{'Rows/sec':>14}")
    for days in DAY_SIZES:
        df = generate_long_format_spend(periods_days=days, rng=np.random.default_rng(RANDOM_SEED))
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        n_rows = len(df)

        times = []
        for _ in range(REPEATS):
            start = time.perf_counter()
            response = client.post(
                "/api/upload",
                files={"file": ("sample.csv", io.BytesIO(csv_bytes), "text/csv")},
            )
            elapsed = time.perf_counter() - start
            assert response.status_code == 200, f"Unexpected status {response.status_code}: {response.text}"
            times.append(elapsed)

        median_time = sorted(times)[len(times) // 2]
        rows_per_sec = n_rows / median_time
        print(f"{days:>6}{n_rows:>10}{median_time:>18.4f}{rows_per_sec:>14,.0f}")


if __name__ == "__main__":
    main()
