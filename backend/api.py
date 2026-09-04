"""
Lightweight FastAPI wrapper exposing HTTP endpoints for the Spendzone frontend.

Run locally with:
    uvicorn api:app --reload --port 8000
"""
import io
import json
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from scipy.optimize import minimize

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
