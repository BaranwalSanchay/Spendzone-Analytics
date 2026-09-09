"""Compare the optimizer's own objective -- sum(w_i * log(x_i + 1)) -- under the actual
historical channel split vs. the optimized split, for identical learned weights and
identical monthly total budget.

This is NOT a claim about observed revenue. Both numbers come from the same in-model
revenue proxy the optimizer itself maximizes, so the optimized split can only ever look
better or equal under it -- it's an upper bound on projected lift under the model's own
assumption, not a validated business result. See 2b (backtest_optimizer.py) for how that
assumption holds up against actual GMV.

Run (from Spendzone-Analytics/, using the ds-pipeline venv):
    Windows: ds-pipeline\\.venv\\Scripts\\python.exe scripts\\metrics\\projected_lift.py
    macOS/Linux: ds-pipeline/.venv/bin/python scripts/metrics/projected_lift.py
"""
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPTIMIZER_MODULE_DIR = os.path.join(REPO_ROOT, "ds-pipeline", "Budget Allocation")
DATA_FILE = os.path.join(REPO_ROOT, "scripts", "sample_data", "Final_monthly.csv")

sys.path.insert(0, OPTIMIZER_MODULE_DIR)
from budget_optimizer import BudgetOptimizer  # noqa: E402


def main():
    optimizer = BudgetOptimizer(data_file=DATA_FILE)
    optimizer.prepare_data()
    optimizer.run_bilevel_optimization()
    results_df = optimizer.generate_allocation_recommendations()

    weights = optimizer.optimal_weights  # raw (un-normalized) weights -- what the objective actually uses

    print(f"\n{'Month':<10}{'Historical Objective':>22}{'Optimized Objective':>22}{'% Difference':>16}")
    diffs = []
    for i, month in enumerate(optimizer.month_years):
        historical_alloc = optimizer.channel_data[i]  # actual $ per channel that month
        historical_obj = np.sum(weights * np.log(historical_alloc + 1))
        optimized_obj = results_df.loc[i, "Projected_Revenue"]  # same objective, optimized split, same total budget
        pct_diff = (optimized_obj - historical_obj) / historical_obj * 100
        diffs.append(pct_diff)
        print(f"{month:<10}{historical_obj:>22.4f}{optimized_obj:>22.4f}{pct_diff:>15.2f}%")

    mean_diff = float(np.mean(diffs))
    print(f"\nMean % difference (optimized vs. historical, in-model objective): {mean_diff:.2f}%")
    print(f"Months compared: {len(diffs)}")


if __name__ == "__main__":
    main()
