"""Count what's actually in scripts/sample_data/ -- rows, months, channels, and
engineered feature groups -- instead of quoting numbers from memory. These are the
sample datasets committed to this repo; the real proprietary data was scrubbed during
the Market-Lens -> Spendzone rebrand, so this is what's reproducible here.

Feature-group classification (spend aggregates / lagged targets / KPI / weather &
holiday context) is done by keyword matching against each dataset's actual columns, not
by hand-picking a description -- see CATEGORY_KEYWORDS below.

Run (from Spendzone-Analytics/):
    python scripts/metrics/dataset_inventory.py
"""
import os

import sys

import pandas as pd

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DATA_DIR = os.path.join(SCRIPTS_DIR, "sample_data")
sys.path.insert(0, SCRIPTS_DIR)
from generate_sample_data import CHANNELS  # noqa: E402 -- single source of truth for channel names

# Order matters: checked top to bottom, first match wins. Lagged/derived target is
# checked before spend aggregate so "gmv_next_minus_investment" (which contains
# "investment") lands in the more specific bucket.
CATEGORY_KEYWORDS = {
    "lagged/derived target": ["next", "minus", "gmv"],
    "spend aggregate": ["investment", "spend"] + [c.lower() for c in CHANNELS],
    "weather/holiday context": ["temp", "rain", "snow", "precip", "deg days", "holiday", "is_holiday"],
    "kpi/business context": ["nps", "stock_index", "sla", "mrp", "list price", "is_sales", "units",
                              "conversions"],
}


def categorize(column: str) -> str:
    col_lower = column.strip().lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in col_lower for kw in keywords):
            return category
    return "identifier/other"


def main():
    files = {
        "sample_marketing_spend.csv": "long-format daily spend (Date, Channel, Spend, Conversions)",
        "Final_monthly.csv": "wide-format monthly budget-optimizer input",
        "Monthly_Master.csv": "wide-format monthly MMM input (Robyn-style, with weather/holiday/KPI context)",
    }

    total_rows = 0
    all_months = set()
    all_channels = set()
    all_engineered = {}

    for filename, description in files.items():
        path = os.path.join(SAMPLE_DATA_DIR, filename)
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        total_rows += len(df)

        print(f"\n{filename} -- {description}")
        print(f"  rows: {len(df)}, columns: {len(df.columns)}")

        if "Month_Year" in df.columns:
            months = set(df["Month_Year"].astype(str))
            all_months |= months
            print(f"  months covered: {len(months)} ({min(months)} to {max(months)})")
        elif "Date" in df.columns:
            dates = pd.to_datetime(df["Date"])
            months = set(dates.dt.to_period("M").astype(str))
            all_months |= months
            print(f"  date range: {dates.min().date()} to {dates.max().date()} ({len(months)} distinct months)")

        if "Channel" in df.columns:
            channels = set(df["Channel"].dropna().unique())
            all_channels |= channels
            print(f"  channels (long format): {len(channels)} -- {sorted(channels)}")
        else:
            # Wide format: channel columns are matched exactly against the known
            # channel list (generate_sample_data.CHANNELS), not by keyword guessing.
            wide_channels = [c for c in df.columns if c.strip() in CHANNELS]
            all_channels |= set(wide_channels)
            print(f"  channels (wide format): {len(wide_channels)} -- {sorted(wide_channels)}")

        categorized = {}
        for col in df.columns:
            if col in ("Month_Year", "Date", "Channel"):
                continue
            categorized.setdefault(categorize(col), []).append(col)
        for category, cols in categorized.items():
            print(f"  {category}: {len(cols)} column(s) -- {cols}")
            all_engineered.setdefault(category, set()).update(cols)

    print(f"\n=== Totals across {len(files)} sample datasets ===")
    print(f"Total rows: {total_rows}")
    print(f"Distinct months covered (union across files): {len(all_months)}")
    print(f"Distinct marketing channels modeled: {len(all_channels)} -- {sorted(all_channels)}")
    for category, cols in all_engineered.items():
        print(f"Engineered feature group '{category}': {len(cols)} distinct column(s)")


if __name__ == "__main__":
    main()
