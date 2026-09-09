"""Run BudgetOptimizer against scripts/sample_data/Final_monthly.csv and populate
Spendzone-Analytics/plots/ with the PNGs and bilevel_optimization_bioptimizer.json that
/api/budget-scenario reads. Without this, plots/ stays empty and that endpoint 503s.

Run (from Spendzone-Analytics/, using the ds-pipeline venv):
    Windows: ds-pipeline\\.venv\\Scripts\\python.exe scripts\\metrics\\run_optimizer.py
    macOS/Linux: ds-pipeline/.venv/bin/python scripts/metrics/run_optimizer.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPTIMIZER_MODULE_DIR = os.path.join(REPO_ROOT, "ds-pipeline", "Budget Allocation")
DATA_FILE = os.path.join(REPO_ROOT, "scripts", "sample_data", "Final_monthly.csv")
PLOTS_DIR = os.path.join(REPO_ROOT, "plots")

sys.path.insert(0, OPTIMIZER_MODULE_DIR)
from budget_optimizer import BudgetOptimizer, export_budget_json  # noqa: E402


def main():
    optimizer = BudgetOptimizer(data_file=DATA_FILE)
    optimizer.prepare_data()
    optimizer.run_bilevel_optimization()
    optimizer.generate_allocation_recommendations()

    # save_results() defaults to writing into the caller's cwd -- pointed at PLOTS_DIR
    # explicitly here so the results CSV lands next to the PNGs/JSON it's the source of,
    # rather than wherever this script happened to be invoked from.
    os.makedirs(PLOTS_DIR, exist_ok=True)
    optimizer.save_results(output_file=os.path.join(PLOTS_DIR, "bilevel_optimization_results_constrained.csv"))
    optimizer.visualize_allocations(output_dir=PLOTS_DIR)
    optimizer.visualize_weights(output_dir=PLOTS_DIR)
    optimizer.visualize_weight_comparison(output_dir=PLOTS_DIR)
    export_budget_json(optimizer, "bilevel_optimization_bioptimizer.json", output_dir=PLOTS_DIR)


if __name__ == "__main__":
    main()
