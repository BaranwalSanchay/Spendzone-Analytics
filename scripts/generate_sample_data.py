"""
Generate synthetic sample datasets to exercise Spendzone end-to-end, without
needing the real proprietary marketing data.

Produces three files under Spendzone-Analytics/scripts/sample_data/:

1. sample_marketing_spend.csv
   Long format: Date, Channel, Spend, Conversions.
   This is the exact schema backend/api.py's /api/upload validates
   (REQUIRED_COLUMNS in backend/api.py) and what the dashboard's
   data-upload-card.tsx documents. Use this to test:
     - the frontend uploader + schema validation + data profiling
     - `curl -F file=@sample_marketing_spend.csv http://localhost:8000/api/upload`

2. Final_monthly.csv
   Wide format matching ds-pipeline/Budget Allocation/Budget_Bioptimisation.ipynb's
   BudgetOptimizer/BudgetOptimiserGMV classes (Month_Year, Total Investment,
   gmv_next_minus_investment, and the 7 CHANNELS columns). Drop this next to the
   notebook (or update `data_file=`) to run the bi-level budget optimizer for real.

3. Monthly_Master.csv
   Wide format matching ds-pipeline/Budget Allocation/Robyn.ipynb's expected
   "CSV Input Files/Monthly_Master.csv" input (pre gmv->revenue rename), including
   the weather/holiday/context columns Robyn's MMMDataSpec references.

Run (from Spendzone-Analytics/, using the ds-pipeline venv set up per its README —
pandas/numpy are all this script needs, but it's the venv that has them):
    Windows: ds-pipeline\\.venv\\Scripts\\python.exe scripts\\generate_sample_data.py
    macOS/Linux: ds-pipeline/.venv/bin/python scripts/generate_sample_data.py
"""

import os

import numpy as np
import pandas as pd

RANDOM_SEED = 42
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")

CHANNELS = [
    "TV",
    "Digital",
    "Sponsorship",
    "Content Marketing",
    "Online marketing",
    "Affiliates",
    "SEM",
]

# Roughly how much of the monthly budget each channel tends to get, used to
# shape both the long-format and wide-format spend so they're internally
# consistent (e.g. TV/Online marketing dominate, matching the 50%-cap channels
# BudgetOptimizer treats specially).
CHANNEL_SHARE = {
    "TV": 0.32,
    "Digital": 0.18,
    "Sponsorship": 0.10,
    "Content Marketing": 0.08,
    "Online marketing": 0.20,
    "Affiliates": 0.06,
    "SEM": 0.06,
}

# Rough conversion rate per $ spent, per channel (Conversions ~= Spend * rate),
# used only for the long-format dataset so channel performance differs
# visibly on the dashboard.
CHANNEL_CONV_RATE = {
    "TV": 0.012,
    "Digital": 0.028,
    "Sponsorship": 0.015,
    "Content Marketing": 0.022,
    "Online marketing": 0.030,
    "Affiliates": 0.020,
    "SEM": 0.035,
}


def _month_range(start="2023-07-01", periods=13):
    return pd.date_range(start=start, periods=periods, freq="MS")


def generate_long_format_spend(
    start="2023-07-01",
    periods_days=365,
    rng=None,
) -> pd.DataFrame:
    """Date, Channel, Spend, Conversions — the /api/upload schema."""
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    dates = pd.date_range(start=start, periods=periods_days, freq="D")
    total_daily_budget = 4000 + 1500 * np.sin(np.linspace(0, 6 * np.pi, len(dates)))
    total_daily_budget = np.clip(total_daily_budget, 500, None)

    rows = []
    for date, budget in zip(dates, total_daily_budget):
        for channel in CHANNELS:
            base = budget * CHANNEL_SHARE[channel]
            noise = rng.normal(loc=1.0, scale=0.25)
            spend = round(max(0.0, base * noise), 2)

            rate = CHANNEL_CONV_RATE[channel] * rng.normal(loc=1.0, scale=0.2)
            conversions = int(max(0, round(spend * rate + rng.normal(0, 1.5))))

            rows.append(
                {
                    "Date": date.strftime("%Y-%m-%d"),
                    "Channel": channel,
                    "Spend": spend,
                    "Conversions": conversions,
                }
            )

    df = pd.DataFrame(rows)

    # Sprinkle in a little realistic messiness (missing conversions on a few
    # rows) so the /api/upload profiling endpoint has something to report.
    dirty_idx = rng.choice(df.index, size=int(0.02 * len(df)), replace=False)
    df.loc[dirty_idx, "Conversions"] = np.nan

    return df


def generate_final_monthly(periods=13, rng=None) -> pd.DataFrame:
    """Wide format for Budget_Bioptimisation.ipynb's BudgetOptimizer."""
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    months = _month_range(periods=periods)
    total_investment = 50_000 + 15_000 * np.sin(np.linspace(0, 3 * np.pi, periods)) + rng.normal(0, 2000, periods)
    total_investment = np.clip(total_investment, 20_000, None)

    data = {"Month_Year": months.strftime("%Y-%m")}
    for channel in CHANNELS:
        noise = rng.normal(loc=1.0, scale=0.15, size=periods)
        data[channel] = np.round(total_investment * CHANNEL_SHARE[channel] * noise, 2)

    df = pd.DataFrame(data)
    df["Total Investment"] = df[CHANNELS].sum(axis=1).round(2)

    # gmv_next_minus_investment: a synthetic "incremental GMV" target that
    # correlates with spend (so BudgetOptimizer's correlation-based weight
    # ranges produce sane, non-degenerate results) plus noise.
    channel_weight_truth = {
        "TV": 3.0,
        "Digital": 4.5,
        "Sponsorship": 2.0,
        "Content Marketing": 2.5,
        "Online marketing": 5.0,
        "Affiliates": 1.8,
        "SEM": 4.0,
    }
    signal = sum(df[ch] * w for ch, w in channel_weight_truth.items())
    df["gmv_next_minus_investment"] = (signal + rng.normal(0, signal.std() * 0.1, periods)).round(2)

    return df


def generate_monthly_master(periods=13, rng=None) -> pd.DataFrame:
    """Wide format for Robyn.ipynb's 'CSV Input Files/Monthly_Master.csv' input."""
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    months = _month_range(periods=periods)
    final_monthly = generate_final_monthly(periods=periods, rng=rng)

    order_date_only = [
        m + pd.Timedelta(days=int(rng.integers(1, 27)), hours=int(rng.integers(0, 23)))
        for m in months
    ]

    month_num = months.month.values
    # Simple seasonal curve so temperature-based context vars look plausible
    # for a northern-hemisphere climate (matches the Robyn notebook's
    # Celsius/mm weather columns).
    seasonal = -np.cos(2 * np.pi * (month_num - 1) / 12)
    mean_temp = 12 + 15 * seasonal + rng.normal(0, 1.5, periods)
    max_temp = mean_temp + rng.uniform(4, 9, periods)
    min_temp = mean_temp - rng.uniform(4, 9, periods)

    df = pd.DataFrame(
        {
            "Month_Year": final_monthly["Month_Year"],
            "gmv": (final_monthly["gmv_next_minus_investment"] + final_monthly["Total Investment"]).round(2),
            "units": np.round(rng.uniform(1.0, 1.05, periods), 6),
            "sla": np.round(rng.uniform(5.0, 6.5, periods), 6),
            "product_mrp": np.round(rng.uniform(2200, 4700, periods), 6),
            "product_procurement_sla": np.round(rng.uniform(2.5, 10.5, periods), 6),
            "order_date_only": order_date_only,
            "is_holiday": np.round(rng.uniform(0, 0.1, periods), 6),
            "Month": month_num.astype(float),
            "Mean Temp (°C)": np.round(mean_temp, 1),
            "Heat Deg Days (°C)": np.round(np.clip(mean_temp - 18, 0, None), 1),
            "Cool Deg Days (°C)": np.round(np.clip(18 - mean_temp, 0, None), 1),
            "Total Rain (mm)": np.round(rng.uniform(0, 90, periods), 1),
            "Total Snow (cm)": np.round(np.clip(-seasonal, 0, None) * rng.uniform(0, 25, periods), 1),
            "Total Precip (mm)": np.round(rng.uniform(10, 100, periods), 1),
            "Snow on Grnd (cm)": np.round(np.clip(-seasonal, 0, None) * rng.uniform(0, 15, periods), 1),
            "Total Investment": final_monthly["Total Investment"],
            "TV": final_monthly["TV"],
            "Digital": final_monthly["Digital"],
            "Sponsorship": final_monthly["Sponsorship"],
            "Content Marketing": final_monthly["Content Marketing"],
            "Online marketing": final_monthly["Online marketing"],
            " Affiliates": final_monthly["Affiliates"],  # leading space matches rename_dict's key
            "SEM": final_monthly["SEM"],
            "NPS_Score": np.round(rng.uniform(44, 62, periods), 1),
            "Stock_Index": np.round(rng.uniform(1000, 1260, periods), 0),
            "List Price": np.round(rng.uniform(1500, 3100, periods), 6),
            "Max_Temp_C": np.round(max_temp, 1),
            "Min_Temp_C": np.round(min_temp, 1),
            "is_sales": rng.integers(0, 100_000, periods),
            "Holiday Week": rng.integers(0, 80_000, periods),
        }
    )
    return df


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)

    long_df = generate_long_format_spend(rng=rng)
    long_path = os.path.join(OUTPUT_DIR, "sample_marketing_spend.csv")
    long_df.to_csv(long_path, index=False)
    print(f"Wrote {long_path} ({len(long_df)} rows) — for /api/upload and the dashboard uploader")

    final_monthly_df = generate_final_monthly(rng=np.random.default_rng(RANDOM_SEED))
    final_monthly_path = os.path.join(OUTPUT_DIR, "Final_monthly.csv")
    final_monthly_df.to_csv(final_monthly_path, index=False)
    print(f"Wrote {final_monthly_path} ({len(final_monthly_df)} rows) — for Budget_Bioptimisation.ipynb")

    monthly_master_df = generate_monthly_master(rng=np.random.default_rng(RANDOM_SEED))
    monthly_master_path = os.path.join(OUTPUT_DIR, "Monthly_Master.csv")
    monthly_master_df.to_csv(monthly_master_path, index=False)
    print(f"Wrote {monthly_master_path} ({len(monthly_master_df)} rows) — for Robyn.ipynb")


if __name__ == "__main__":
    main()
