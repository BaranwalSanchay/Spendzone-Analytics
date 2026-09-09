"""Fit the channel-level attribution regression from backend/agents/roi.py's
calculate_channel_roi() against scripts/sample_data/Monthly_Master.csv, identify
channels with a negative marginal-ROI coefficient, and report what share of total
spend those channels absorb.

This reimplements roi.py's regression method (multivariate LinearRegression of monthly
GMV on channel spend, fit twice: once against the same month's GMV, once against next
month's GMV) directly against the sample CSV -- it does not go through ROIAgent or the
LLM tool-calling layer, so it needs no API key. It intentionally drops two pieces of
roi.py's logic that are specific to the original proprietary dataset and don't apply
here:

  1. roi.py multiplies investment columns by 1e7 to convert crore-denominated spend to
     rupees. scripts/sample_data/Monthly_Master.csv's "Total Investment" and channel
     columns are already in the same units as "gmv" (tens of thousands, not crores) --
     applying that factor would inflate spend ~1e7x relative to GMV and produce
     meaningless coefficients.
  2. roi.py hardcodes excluding specific months ('2023-05', '2023-06', '2024-07') from
     the two regressions -- an adjustment tied to anomalies in the original dataset's
     date range. Monthly_Master.csv's 13 months (2023-07 through 2024-07) don't contain
     those anomalies, so no months are excluded here.

roi.py's default channel list (["TV", "Radio", ..., "Other"]) also doesn't match this
dataset's columns (no Radio/Other column exists; roi.py's own missing-column check would
reject those defaults against this data). This script uses the 7 channels that actually
exist in Monthly_Master.csv instead.

Run (from Spendzone-Analytics/, using the ds-pipeline venv):
    Windows: ds-pipeline\\.venv\\Scripts\\python.exe scripts\\metrics\\roi_regression.py
    macOS/Linux: ds-pipeline/.venv/bin/python scripts/metrics/roi_regression.py
"""
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(REPO_ROOT, "scripts", "sample_data", "Monthly_Master.csv")

CHANNELS = ["TV", "Digital", "Sponsorship", "Content Marketing", "Online marketing", " Affiliates", "SEM"]
DATE_COLUMN = "order_date_only"
GMV_COLUMN = "gmv"
INVESTMENT_COLUMN = "Total Investment"


def fit_and_report(label, X_df, y):
    model = LinearRegression(fit_intercept=True)
    model.fit(X_df.values, y)
    coefs = dict(zip(X_df.columns, model.coef_))

    print(f"\n{label} (n={len(y)} months, intercept={model.intercept_:,.2f}):")
    print(f"{'Channel':<22}{'Coefficient':>16}{'Avg Monthly Spend':>20}")
    negative_spend = 0.0
    total_spend = 0.0
    for channel in X_df.columns:
        avg_spend = X_df[channel].mean()
        total_spend += avg_spend
        marker = ""
        if coefs[channel] < 0:
            negative_spend += avg_spend
            marker = "  (negative marginal ROI)"
        print(f"{channel.strip():<22}{coefs[channel]:>16.4f}{avg_spend:>20,.2f}{marker}")

    negative_share = negative_spend / total_spend * 100
    print(f"Spend share absorbed by negative-marginal-ROI channels: {negative_share:.2f}%")
    return coefs, negative_share


def main():
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()
    date_col = DATE_COLUMN
    channels = [c.strip() for c in CHANNELS]
    investment_col = INVESTMENT_COLUMN

    df[date_col] = pd.to_datetime(df[date_col])
    df["year_month"] = df[date_col].dt.to_period("M")
    monthly = df.groupby("year_month").agg({
        GMV_COLUMN: "sum",
        investment_col: "mean",
        **{c: "mean" for c in channels},
    })

    print(f"Loaded {DATA_FILE}")
    print(f"Months after monthly aggregation: {len(monthly)}")

    # Current-month model: this month's channel spend -> this month's GMV.
    fit_and_report("Current-month model (spend -> same-month GMV)", monthly[channels], monthly[GMV_COLUMN].values)

    # Next-month model: this month's channel spend -> next month's GMV.
    next_month = monthly.copy()
    next_month["next_month_gmv"] = next_month[GMV_COLUMN].shift(-1)
    next_month = next_month.dropna(subset=["next_month_gmv"])
    fit_and_report(
        "Next-month model (spend -> following month's GMV)",
        next_month[channels],
        next_month["next_month_gmv"].values,
    )

    print(f"\nCAVEAT: n={len(monthly)} monthly observations against {len(channels)} channel")
    print("predictors -- this regression is poorly identified (few observations per")
    print("coefficient, likely multicollinear channel spend). Coefficient signs and")
    print("magnitudes should be read as indicative, not as validated attribution.")


if __name__ == "__main__":
    main()
