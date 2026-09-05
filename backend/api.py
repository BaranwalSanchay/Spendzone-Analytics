"""
Lightweight FastAPI wrapper exposing HTTP endpoints for the Spendzone frontend.

Run locally with:
    uvicorn api:app --reload --port 8000
"""
import io
import json
import os
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from scipy.optimize import minimize

from utils.report import section_questions

app = FastAPI(title="Spendzone API")

# In production, replace "*" with the deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_COLUMNS = ["Date", "Channel", "Spend", "Conversions"]


class ColumnProfile(BaseModel):
    column: str
    dtype: str
    cardinality: int
    missing_pct: float
    std_dev: Optional[float]


class UploadResponse(BaseModel):
    filename: str
    row_count: int
    columns: list[str]
    channels: list[str]
    date_range: dict[str, Optional[str]]
    profile: list[ColumnProfile]


def profile_dataframe(df: pd.DataFrame) -> List[ColumnProfile]:
    """Automated data profiling for the dashboard's data catalog: cardinality,
    missingness percentage, and standard deviation (numeric columns only) for
    every column, computed at ingestion time for all uploaded marketing data."""
    n_rows = len(df)
    profiles = []
    for col in df.columns:
        series = df[col]
        missing_pct = float(series.isna().mean() * 100) if n_rows else 0.0
        is_numeric = pd.api.types.is_numeric_dtype(series)
        std_dev = float(series.std()) if is_numeric and series.notna().any() else None
        profiles.append(
            ColumnProfile(
                column=col,
                dtype=str(series.dtype),
                cardinality=int(series.nunique(dropna=True)),
                missing_pct=round(missing_pct, 2),
                std_dev=round(std_dev, 4) if std_dev is not None else None,
            )
        )
    return profiles


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_marketing_spend(file: UploadFile = File(...)):
    """Validate and profile an uploaded marketing spend CSV.

    Required schema: Date, Channel, Spend, Conversions
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")

    df.columns = df.columns.str.strip()
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                f"CSV is missing required column(s): {', '.join(missing)}. "
                f"Expected schema: {', '.join(REQUIRED_COLUMNS)}."
            ),
        )

    dates = pd.to_datetime(df["Date"], errors="coerce")
    if dates.isna().all():
        raise HTTPException(status_code=422, detail="Could not parse any values in the 'Date' column.")

    return UploadResponse(
        filename=file.filename,
        row_count=len(df),
        columns=list(df.columns),
        channels=sorted(df["Channel"].dropna().astype(str).unique().tolist()),
        date_range={
            "start": dates.min().date().isoformat() if dates.notna().any() else None,
            "end": dates.max().date().isoformat() if dates.notna().any() else None,
        },
        profile=profile_dataframe(df),
    )


# --- Prescriptive "what-if" budget scenario modeling -----------------------------------
#
# Mirrors BudgetOptimizer.lower_level_optimization() in
# ds-pipeline/Budget Allocation/Budget_Bioptimisation.ipynb: given a set of pre-calculated
# bi-level optimization channel weights, find the dollar split of a total budget that
# maximizes sum(weight_i * log(allocation_i + 1)), the same log-based diminishing-returns
# revenue model used there, subject to the same channel constraints.

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "plots" / "bilevel_optimization_bioptimizer.json"
UPPER_BOUND_CHANNELS = {"TV": 0.5, "Online marketing": 0.5}  # max 50% of budget, as in the notebook


class ChannelWeight(BaseModel):
    channel: str
    weight: float


class BudgetScenarioRequest(BaseModel):
    total_budget: float = Field(..., gt=0)
    # Optional: pass explicit weights (e.g. {"channel": "TV", "weight": 0.42}). If omitted,
    # falls back to the notebook's exported bilevel_optimization_bioptimizer.json.
    weights: Optional[List[ChannelWeight]] = None


class ChannelAllocation(BaseModel):
    channel: str
    amount: float
    percentage: float


class BudgetScenarioResponse(BaseModel):
    total_budget: float
    allocations: List[ChannelAllocation]


def _load_default_weights() -> List[ChannelWeight]:
    if not DEFAULT_WEIGHTS_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "No pre-calculated budget weights found. Run Budget_Bioptimisation.ipynb "
                "to generate Spendzone-Analytics/plots/bilevel_optimization_bioptimizer.json, "
                "or pass `weights` explicitly in the request body."
            ),
        )
    with open(DEFAULT_WEIGHTS_PATH) as f:
        payload = json.load(f)
    return [ChannelWeight(channel=w["channel"], weight=w["normalized_weight"]) for w in payload["weights"]]


@app.post("/api/budget-scenario", response_model=BudgetScenarioResponse)
def budget_scenario(request: BudgetScenarioRequest):
    """Given a total budget and the pre-calculated bi-level optimization weights,
    return the exact recommended dollar split across channels."""
    weights = request.weights or _load_default_weights()
    if not weights:
        raise HTTPException(status_code=400, detail="No channel weights available.")

    channels = [w.channel for w in weights]
    weight_values = np.array([w.weight for w in weights], dtype=float)
    n = len(channels)

    def objective(allocations):
        allocations = np.abs(allocations)
        allocations = allocations / np.sum(allocations) * request.total_budget
        revenue = np.sum(weight_values * np.log(allocations + 1))
        return -revenue

    constraints = [{"type": "eq", "fun": lambda a: np.sum(a) - 1.0}]
    for channel_name, upper_bound in UPPER_BOUND_CHANNELS.items():
        if channel_name in channels:
            idx = channels.index(channel_name)
            constraints.append({
                "type": "ineq",
                "fun": lambda a, idx=idx, bound=upper_bound: bound - a[idx],
            })

    result = minimize(
        objective,
        np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.001, 1.0) for _ in range(n)],
        constraints=constraints,
        options={"disp": False, "maxiter": 1000},
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=f"Optimization did not converge: {result.message}")

    percentages = result.x / np.sum(result.x)
    amounts = percentages * request.total_budget

    return BudgetScenarioResponse(
        total_budget=request.total_budget,
        allocations=[
            ChannelAllocation(channel=ch, amount=float(amt), percentage=float(pct * 100))
            for ch, amt, pct in zip(channels, amounts, percentages)
        ],
    )


# --- AI-powered report generation --------------------------------------------------
#
# Wraps backend/main.py's generate_markdown_report() (the LangGraph multi-agent
# report generator) as a background job: a real run makes several LLM calls per
# section plus deliberate rate-limit pauses, so it can take minutes -- far too long
# to block an HTTP request on. The heavy agents/langchain import only happens inside
# the background job itself, so importing this module (and every other endpoint above)
# stays cheap regardless of whether report generation is ever used.
#
# Single job at a time: the pipeline shares a process-wide DataManager singleton and one
# SQLite file for its SQL agent (backend/agents/sql.py), so two concurrent runs would
# corrupt each other's data rather than actually run in parallel. This in-memory job
# store also resets on server restart -- there's no persistence/queue infrastructure
# here, which is fine for a single-instance deployment but wouldn't scale past one.

BACKEND_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BACKEND_DIR / "reports"
DATA_DIR = BACKEND_DIR / "data"
SQL_DB_PATH = DATA_DIR / "marketing_analysis.db"
# A directory (not a single file) since DataManager already supports loading every CSV in
# a directory as its own named table (utils/data_manager.py) -- multiple uploads become
# multiple tables the SQL agent can query, keyed by original filename.
UPLOADED_DATASET_DIR = DATA_DIR / "uploaded_dataset"


class ReportJob(BaseModel):
    job_id: str
    status: str  # "running" | "completed" | "failed"
    created_at: str
    completed_at: Optional[str] = None
    sections_done: int = 0
    total_sections: int = len(section_questions)
    current_section: Optional[str] = None
    error: Optional[str] = None


_report_jobs: dict[str, ReportJob] = {}
_report_jobs_lock = threading.Lock()
_report_job_running = False


def _run_report_job(job_id: str, data_path: Optional[str]) -> None:
    global _report_job_running

    # Imported here, not at module load, so the rest of the API stays fast to start and
    # doesn't require langchain/langgraph to even be importable unless this job actually runs.
    from main import generate_markdown_report
    from utils.data_manager import DataManager
    from utils.report_to_pdf import markdown_to_pdf

    job = _report_jobs[job_id]

    def on_progress(section: str, done: int, total: int) -> None:
        job.current_section = section
        job.sections_done = done
        job.total_sections = total

    try:
        # DataManager is a process-wide singleton (utils/data_manager.py) -- without
        # resetting it, a second report run would silently keep analyzing the *first*
        # run's dataset instead of picking up this job's data_path.
        DataManager._instance = None
        # agents/sql.py skips re-importing a table name that already exists, so a
        # leftover SQLite file would otherwise keep the SQL agent answering from
        # whatever dataset first created it, regardless of new uploads.
        if SQL_DB_PATH.exists():
            SQL_DB_PATH.unlink()

        md_path = REPORTS_DIR / f"{job_id}.md"
        generate_markdown_report(data_path=data_path, output_path=md_path, on_progress=on_progress)

        pdf_path = REPORTS_DIR / f"{job_id}.pdf"
        markdown_to_pdf(md_path, pdf_path, title="Marketing Analysis Report")

        job.status = "completed"
    except Exception as exc:  # noqa: BLE001 -- reported via the job's `error` field
        job.status = "failed"
        job.error = str(exc)
    finally:
        job.completed_at = datetime.now(timezone.utc).isoformat()
        with _report_jobs_lock:
            _report_job_running = False


@app.post("/api/reports/generate", response_model=ReportJob, status_code=202)
async def generate_report(background_tasks: BackgroundTasks, files: Optional[List[UploadFile]] = File(None)):
    """Start a report-generation job. Optionally upload one or more CSVs (or leave it out
    to use whatever dataset is already configured in backend/data/) -- poll
    GET /api/reports/{job_id} for progress, then GET .../markdown or .../pdf once status is
    "completed". Each uploaded file becomes its own named table (by filename) the SQL agent
    can query -- e.g. uploading Monthly_Master.csv and Final_monthly.csv together gives the
    agents two related tables instead of just one.

    Note: this dataset is the company's broader operations data (orders, GMV, NPS, SLA,
    marketing spend, etc. -- whatever columns the agents/ modules query), not the simple
    Date/Channel/Spend/Conversions schema /api/upload validates for the dashboard.
    """
    global _report_job_running

    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="GROQ_API_KEY is not configured on the server; report generation is unavailable.",
        )

    with _report_jobs_lock:
        if _report_job_running:
            raise HTTPException(
                status_code=409,
                detail="A report is already being generated. Wait for it to finish before starting another.",
            )
        _report_job_running = True

    # Needed unconditionally: agents/sql.py's SQL agent always opens a SQLite file under
    # backend/data/ regardless of whether a custom CSV is uploaded, and sqlite3 fails with
    # an opaque "unable to open database file" if that directory doesn't exist yet.
    DATA_DIR.mkdir(exist_ok=True)

    data_path = None
    uploads = [f for f in (files or []) if f is not None and f.filename]
    if uploads:
        bad = [f.filename for f in uploads if not f.filename.lower().endswith(".csv")]
        if bad:
            with _report_jobs_lock:
                _report_job_running = False
            raise HTTPException(status_code=400, detail=f"Only CSV files are supported (got: {', '.join(bad)}).")

        # Clear any files left over from a previous run rather than accumulating uploads
        # across jobs indefinitely.
        if UPLOADED_DATASET_DIR.exists():
            shutil.rmtree(UPLOADED_DATASET_DIR)
        UPLOADED_DATASET_DIR.mkdir(parents=True)

        for upload in uploads:
            dest = UPLOADED_DATASET_DIR / Path(upload.filename).name  # strip any path components
            with open(dest, "wb") as f:
                f.write(await upload.read())
        data_path = str(UPLOADED_DATASET_DIR)

    job_id = uuid.uuid4().hex[:12]
    job = ReportJob(
        job_id=job_id,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        total_sections=len(section_questions),
    )
    _report_jobs[job_id] = job
    background_tasks.add_task(_run_report_job, job_id, data_path)
    return job


@app.get("/api/reports/latest", response_model=Optional[ReportJob])
def get_latest_report_job():
    """So the frontend can show the most recent report after a page refresh without
    tracking a job_id client-side. In-memory only -- resets on server restart."""
    if not _report_jobs:
        return None
    return max(_report_jobs.values(), key=lambda j: j.created_at)


@app.get("/api/reports/{job_id}", response_model=ReportJob)
def get_report_job(job_id: str):
    job = _report_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No such report job.")
    return job


@app.get("/api/reports/{job_id}/markdown", response_class=PlainTextResponse)
def get_report_markdown(job_id: str):
    job = _report_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No such report job.")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"Report is not ready yet (status: {job.status}).")
    md_path = REPORTS_DIR / f"{job_id}.md"
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Report markdown file not found.")
    return md_path.read_text(encoding="utf-8")


@app.get("/api/reports/{job_id}/pdf")
def get_report_pdf(job_id: str):
    job = _report_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No such report job.")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"Report is not ready yet (status: {job.status}).")
    pdf_path = REPORTS_DIR / f"{job_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report PDF file not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename="marketing-analysis-report.pdf")
