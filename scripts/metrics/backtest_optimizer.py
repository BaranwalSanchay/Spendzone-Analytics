"""Held-out backtest for BudgetOptimizer: train the bilevel-optimization weights on all
but the final K months, project the target (gmv_next_minus_investment, the same column
the optimizer's own upper_level_objective tries to track) for those K held-out months
using only each month's actual total investment, and score against two naive baselines.

With 13 monthly rows total this is a tiny holdout by any standard -- these numbers are
reported as indicative, not as a validated out-of-sample result.

Method for turning the optimizer's unitless log-objective into a GMV-scale prediction:
this mirrors what BudgetOptimizer.upper_level_objective() already does internally (fit
weights, then scale predicted objective values to the actual target's mean) -- computed
here explicitly on the training split only, then applied to the untouched test months.

Run (from Spendzone-Analytics/, using the ds-pipeline venv):
    Windows: ds-pipeline\\.venv\\Scripts\\python.exe scripts\\metrics\\backtest_optimizer.py
    macOS/Linux: ds-pipeline/.venv/bin/python scripts/metrics/backtest_optimizer.py
"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_percentage_error, root_mean_squared_error

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPTIMIZER_MODULE_DIR = os.path.join(REPO_ROOT, "ds-pipeline", "Budget Allocation")
DATA_FILE = os.path.join(REPO_ROOT, "scripts", "sample_data", "Final_monthly.csv")

sys.path.insert(0, OPTIMIZER_MODULE_DIR)
from budget_optimizer import BudgetOptimizer  # noqa: E402

K_HOLDOUT = 3  # of 13 total months -- see caveat in the module docstring


def score(name, actual, predicted):
    r2 = r2_score(actual, predicted)
    mape = mean_absolute_percentage_error(actual, predicted) * 100
    rmse = root_mean_squared_error(actual, predicted)
    print(f"{name:<20}{'R2':>10}: {r2:>10.4f}   {'MAPE':>6}: {mape:>8.2f}%   {'RMSE':>6}: {rmse:>12,.2f}")
    return r2, mape, rmse


def main():
    full_df = pd.read_csv(DATA_FILE)
    n = len(full_df)
    train_df = full_df.iloc[: n - K_HOLDOUT].reset_index(drop=True)
    test_df = full_df.iloc[n - K_HOLDOUT :].reset_index(drop=True)
    print(f"Total months: {n}, training months: {len(train_df)}, held-out months: {len(test_df)}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        train_df.to_csv(tmp.name, index=False)
        train_path = tmp.name

    try:
        optimizer = BudgetOptimizer(data_file=train_path)
        optimizer.prepare_data()
        optimizer.run_bilevel_optimization()
        train_results = optimizer.generate_allocation_recommendations()
    finally:
        os.unlink(train_path)

    # Scale factor calibrated on the training window only, same approach as
    # upper_level_objective() but computed after training is finished, not during it.
    train_actual_mean = train_df["gmv_next_minus_investment"].mean()
    train_predicted_mean = train_results["Projected_Revenue"].mean()
    scaling_factor = train_actual_mean / train_predicted_mean

    predicted_gmv = []
    for _, row in test_df.iterrows():
        total_inv = row["Total Investment"]
        _, _, predicted_revenue = optimizer.lower_level_optimization(optimizer.optimal_weights, None, total_inv)
        predicted_gmv.append(predicted_revenue * scaling_factor)
    predicted_gmv = np.array(predicted_gmv)
    actual_gmv = test_df["gmv_next_minus_investment"].values

    # Persistence baseline: each held-out month predicted as the previous month's actual
    # (walk-forward using true history, not the model's own prior prediction).
    prev_actuals = pd.concat([train_df["gmv_next_minus_investment"].iloc[-1:], test_df["gmv_next_minus_investment"]]).values
    persistence_pred = prev_actuals[:-1]

    # Mean baseline: training-set average applied to every held-out month.
    mean_pred = np.full(K_HOLDOUT, train_actual_mean)

    print(f"\nTraining-set actual mean (gmv_next_minus_investment): {train_actual_mean:,.2f}")
    print(f"Held-out months: {test_df['Month_Year'].tolist()}")
    print(f"Actual values:    {[round(v, 2) for v in actual_gmv]}")
    print(f"Model predicted:  {[round(v, 2) for v in predicted_gmv]}")
    print(f"Persistence pred: {[round(v, 2) for v in persistence_pred]}")
    print(f"Mean pred:        {[round(v, 2) for v in mean_pred]}\n")

    score("BudgetOptimizer", actual_gmv, predicted_gmv)
    score("Persistence", actual_gmv, persistence_pred)
    score("Mean", actual_gmv, mean_pred)

    print(f"\nCAVEAT: n={K_HOLDOUT} held-out points. R2/MAPE/RMSE at this sample size are")
    print("indicative only, not a validated measure of predictive accuracy.")


if __name__ == "__main__":
    main()
