"""BudgetOptimizer, extracted from Budget_Bioptimisation.ipynb so it can be imported
by scripts/metrics/run_optimizer.py instead of re-implemented or executed via nbconvert.

This is a straight lift of the BudgetOptimizer class and export_budget_json() from the
notebook's single code cell -- same bilevel optimization (SLSQP for the per-month
allocation given a set of weights, L-BFGS-B over the weights themselves), same
sum(w_i * log(x_i + 1)) revenue model, same channel bounds. BudgetOptimiserGMV, the
notebook's second class, isn't included here: it depends on Monthly_updated.csv, which
doesn't exist in this repo, and nothing downstream (the API, the frontend) uses it.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import random
import os
import json
from datetime import datetime, timezone

# Default output directory: Spendzone-Analytics/plots, resolved relative to this file
# rather than the caller's cwd so it works the same whether this is imported from the
# notebook's own directory or from scripts/metrics/.
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "plots")


class BudgetOptimizer:
    def __init__(self, data_file="Final_monthly.csv", random_seed=42):
        # Configuration
        self.CHANNELS = ["TV", "Digital", "Sponsorship", "Content Marketing",
                         "Online marketing", "Affiliates", "SEM"]  # Removed "Radio" and "Other"
        self.RANDOM_SEED = random_seed

        # Channels with upper bound constraints
        self.UPPER_BOUND_CHANNELS = {
            "TV": 0.5,  # 50% max allocation
            "Online marketing": 0.5  # 50% max allocation
        }

        # Set random seed for reproducibility
        np.random.seed(self.RANDOM_SEED)
        random.seed(self.RANDOM_SEED)

        # Data attributes
        self.data_file = data_file
        self.df = None
        self.existing_channels = []
        self.num_channels = 0
        self.total_investments = None
        self.gmv_values = None
        self.num_months = 0
        self.month_years = None
        self.channel_data = None
        self.channel_percentages = None
        self.avg_percentages = None
        self.weight_ranges = {}

        # Results
        self.optimal_weights = None
        self.normalized_weights = None
        self.results_df = None

    def prepare_data(self):
        """Load and prepare data for optimization"""
        self.df = pd.read_csv(self.data_file)
        self.df.columns = self.df.columns.str.strip()

        # Filter existing channels
        self.existing_channels = [col for col in self.CHANNELS if col in self.df.columns]
        self.num_channels = len(self.existing_channels)

        # Get total investments and GMV
        self.total_investments = self.df["Total Investment"].values
        self.gmv_values = self.df["gmv_next_minus_investment"].values if "gmv_next_minus_investment" in self.df.columns else None

        self.num_months = len(self.total_investments)

        # Extract month/year information for better reporting
        self.month_years = self.df["Month_Year"].values if "Month_Year" in self.df.columns else [f"Month {i+1}" for i in range(self.num_months)]

        # Analyze historical data to understand channel effectiveness
        self.channel_data = self.df[self.existing_channels].values
        self.channel_percentages = self.channel_data / np.sum(self.channel_data, axis=1)[:, np.newaxis]

        # Calculate historical average allocation percentages
        self.avg_percentages = np.mean(self.channel_percentages, axis=0)

        self._calculate_weight_ranges()

    def _calculate_weight_ranges(self):
        """Calculate correlation between channel investment and GMV to establish weight ranges"""
        if self.gmv_values is not None:
            for i, channel in enumerate(self.existing_channels):
                correlation = np.corrcoef(self.channel_data[:, i], self.gmv_values)[0, 1]
                base_weight = max(0.001, correlation)

                # Define a reasonable range around the correlation coefficient
                # Lower bound: 50% of base weight, Upper bound: 150% of base weight
                self.weight_ranges[channel] = (max(0.001, base_weight * 0.5), base_weight * 1.5)
        else:
            # If GMV not available, use equal effectiveness with wide ranges
            for channel in self.existing_channels:
                self.weight_ranges[channel] = (0.001, 2.0)

    def get_weights_from_params(self, weight_params):
        """Convert optimization parameters to channel weights"""
        weights = np.zeros(self.num_channels)
        for i, channel in enumerate(self.existing_channels):
            min_w, max_w = self.weight_ranges[channel]
            # Scale the parameter (0-1) to the weight range
            weights[i] = min_w + weight_params[i] * (max_w - min_w)
        return weights

    def lower_level_optimization(self, weights, month_idx, total_inv):
        """
        Find optimal allocations given a set of weights and total investment
        """
        def objective_function(allocations):
            """
            Maximize revenue based on allocations and effectiveness
            Revenue model: sum(w_i * log(x_i + 1))
            """
            # Ensure allocations are positive and sum to total investment
            allocations = np.abs(allocations)
            allocations = allocations / np.sum(allocations) * total_inv

            # Calculate revenue using log-based diminishing returns model
            revenue = np.sum(weights * np.log(allocations + 1))

            # We minimize the negative revenue
            return -revenue

        def constraint_sum(allocations):
            """Constraint: Sum of allocations should equal 1 (will be scaled later)"""
            return np.sum(allocations) - 1.0

        # Create constraints for TV and Online marketing upper bounds
        constraints = [{'type': 'eq', 'fun': constraint_sum}]

        # Add upper bound constraints for specific channels
        for channel_name, upper_bound in self.UPPER_BOUND_CHANNELS.items():
            if channel_name in self.existing_channels:
                channel_idx = self.existing_channels.index(channel_name)

                # Create a constraint function for this channel's upper bound
                def channel_upper_bound(allocations, idx=channel_idx, bound=upper_bound):
                    """Constraint: Channel allocation should not exceed the upper bound"""
                    return bound - allocations[idx]

                constraints.append({
                    'type': 'ineq',
                    'fun': channel_upper_bound
                })

        # Initial guess: use historical averages or equal allocation
        initial_guess = self.avg_percentages if len(self.avg_percentages) > 0 else np.ones(self.num_channels) / self.num_channels

        # Bounds: ensure all allocations are positive (0 to 100%)
        bounds = [(0.001, 1.0) for _ in range(self.num_channels)]

        # Optimize
        result = minimize(
            objective_function,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'disp': False, 'maxiter': 1000}
        )

        # Scale optimized percentages to total investment
        opt_percentages = result.x / np.sum(result.x)
        opt_allocations = opt_percentages * total_inv
        revenue = -result.fun

        return opt_percentages, opt_allocations, revenue

    def upper_level_objective(self, weight_params):
        """
        Objective function for the upper-level optimization.
        Find weights that maximize predictive performance across all months.
        """
        # Convert parameters to weights
        weights = self.get_weights_from_params(weight_params)

        # Variable to store performance metric
        total_prediction_error = 0
        predicted_gmvs = []

        # Calculate allocations and predicted GMV for each month
        for month_idx in range(self.num_months - 1):  # Use all but last month for training
            total_inv = self.total_investments[month_idx]

            # Get optimal allocations for these weights
            _, allocations, predicted_revenue = self.lower_level_optimization(weights, month_idx, total_inv)

            # Store predicted revenue as proxy for GMV
            predicted_gmvs.append(predicted_revenue)

        # Calculate error between predicted and actual GMV trend
        if self.gmv_values is not None:
            # Scale predicted revenues to match the scale of GMV
            scaling_factor = np.mean(self.gmv_values[:-1]) / np.mean(predicted_gmvs) if np.mean(predicted_gmvs) > 0 else 1
            scaled_predictions = np.array(predicted_gmvs) * scaling_factor

            # Calculate error between scaled predictions and actual GMV
            errors = scaled_predictions - self.gmv_values[:-1]
            total_prediction_error = np.sum(errors**2)  # Sum of squared errors
        else:
            # If no GMV data, optimize for maximum predicted revenue
            total_prediction_error = -np.sum(predicted_gmvs)

        return total_prediction_error

    def run_bilevel_optimization(self):
        """
        Run the bilevel optimization to find optimal weights and allocations
        """
        print("Starting bilevel optimization to find optimal weights...")
        print(f"Note: Upper bounds set for channels: {self.UPPER_BOUND_CHANNELS}")
        print(f"Channels 'Radio' and 'Other' excluded from analysis.")

        # Initial guess for weight parameters (scaled to 0-1 range)
        initial_weight_params = np.ones(self.num_channels) * 0.5  # Start in the middle of each range

        # Bounds for weight parameters (0-1, will be scaled to actual weight ranges)
        weight_bounds = [(0, 1) for _ in range(self.num_channels)]

        # Optimize weights
        upper_result = minimize(
            self.upper_level_objective,
            initial_weight_params,
            method='L-BFGS-B',  # Different method more suited for upper level
            bounds=weight_bounds,
            options={'disp': True, 'maxiter': 100}
        )

        # Get optimal weights
        optimal_weight_params = upper_result.x
        self.optimal_weights = self.get_weights_from_params(optimal_weight_params)

        # Normalize weights for reporting
        self.normalized_weights = self.optimal_weights / np.sum(self.optimal_weights)

        print("\nOptimal weights found:")
        for i, channel in enumerate(self.existing_channels):
            print(f"{channel}: Raw Weight = {self.optimal_weights[i]:.6f}, Normalized = {self.normalized_weights[i]:.6f}")

        return self.optimal_weights, self.normalized_weights

    def generate_allocation_recommendations(self):
        """Process each month with optimal weights to generate final allocation recommendations"""
        if self.optimal_weights is None or self.normalized_weights is None:
            print("Error: Must run bilevel optimization first")
            return None

        all_results = []
        for month_idx in range(self.num_months):
            total_inv = self.total_investments[month_idx]
            month_year = self.month_years[month_idx]

            # Optimize allocations using the optimal weights
            percentages, allocations, revenue = self.lower_level_optimization(
                self.optimal_weights, month_idx, total_inv
            )

            # Store results
            month_result = {
                'Month': month_year,
                'Total_Investment': total_inv,
                'Projected_Revenue': revenue
            }

            # Add channel allocations
            for i, channel in enumerate(self.existing_channels):
                month_result[f'{channel}_Allocation'] = allocations[i]
                month_result[f'{channel}_Percentage'] = percentages[i] * 100
                month_result[f'{channel}_Raw_Weight'] = self.optimal_weights[i]
                month_result[f'{channel}_Normalized_Weight'] = self.normalized_weights[i]

            all_results.append(month_result)

            # Print formatted results
            print(f"\nMonth: {month_year} (Investment: {total_inv:,.2f})")
            for i, channel in enumerate(self.existing_channels):
                print(f"{channel+':':<20} Allocation: {allocations[i]:>10,.2f}, "
                      f"Percentage: {percentages[i]*100:>6.2f}%, "
                      f"Raw Weight: {self.optimal_weights[i]:>8.6f}, "
                      f"Norm Weight: {self.normalized_weights[i]:>8.6f}")
            print(f"Projected Revenue Value: {revenue:,.2f}")

        # Create a DataFrame with all results
        self.results_df = pd.DataFrame(all_results)
        return self.results_df

    def save_results(self, output_file="bilevel_optimization_results_constrained.csv"):
        """Save optimization results to CSV"""
        if self.results_df is None:
            print("Error: No results to save. Run generate_allocation_recommendations first.")
            return

        self.results_df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")

    def visualize_allocations(self, filename="bilevel_budget_allocation_constrained.png", output_dir=None):
        """Generate visualization of the allocation"""
        if self.results_df is None:
            print("Error: No results to visualize. Run generate_allocation_recommendations first.")
            return

        plt.figure(figsize=(12, 8))

        # Prepare data for stacked bar chart
        month_labels = self.results_df['Month'].values
        allocation_data = {channel: self.results_df[f'{channel}_Allocation'].values
                          for channel in self.existing_channels}

        # Create stacked bar chart
        bottom = np.zeros(self.num_months)
        for channel in self.existing_channels:
            plt.bar(month_labels, allocation_data[channel], bottom=bottom, label=channel)
            bottom += allocation_data[channel]

        plt.title('Optimized Marketing Budget Allocation by Month (Constrained Bilevel Optimization)')
        plt.xlabel('Month')
        plt.ylabel('Allocation Amount')
        plt.legend(loc='upper right')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot
        output_path = os.path.join(output_dir or OUTPUT_DIR, filename)
        plt.savefig(output_path)
        plt.close()
        print(f"Visualization saved as {output_path}")

    def visualize_weights(self, filename="bilevel_channel_weights_constrained.png", output_dir=None):
        """Create a visualization for weights"""
        if self.optimal_weights is None:
            print("Error: No weights to visualize. Run bilevel optimization first.")
            return

        plt.figure(figsize=(10, 6))

        # Plot bar chart of channel weights
        plt.bar(self.existing_channels, self.optimal_weights)
        plt.title('Optimal Channel Weights (Constrained Bilevel Optimization)')
        plt.xlabel('Channel')
        plt.ylabel('Weight Value')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save weight plot
        output_path = os.path.join(output_dir or OUTPUT_DIR, filename)
        plt.savefig(output_path)
        plt.close()
        print(f"Channel weights visualization saved as {output_path}")

    def visualize_weight_comparison(self, filename="weight_comparison_constrained.png", output_dir=None):
        """Create visualization comparing initial weight ranges and optimal weights"""
        if self.optimal_weights is None or not self.weight_ranges:
            print("Error: Missing data for visualization. Run bilevel optimization first.")
            return

        plt.figure(figsize=(12, 6))

        # Width of the bars
        bar_width = 0.35

        # Positions for the bars
        index = np.arange(self.num_channels)

        # Plot initial weight ranges
        lower_bounds = np.array([self.weight_ranges[ch][0] for ch in self.existing_channels])
        upper_bounds = np.array([self.weight_ranges[ch][1] for ch in self.existing_channels])

        # Plot bars for weight ranges
        plt.bar(index, upper_bounds - lower_bounds, bar_width, bottom=lower_bounds, alpha=0.5,
                color='gray', label='Initial Weight Range')

        # Plot markers for optimal weights
        plt.bar(index + bar_width, self.optimal_weights, bar_width, color='blue',
                label='Optimal Weight')

        plt.xlabel('Channel')
        plt.ylabel('Weight Value')
        plt.title('Initial Weight Ranges vs. Optimal Weights (With Constraints)')
        plt.xticks(index + bar_width/2, self.existing_channels, rotation=45)
        plt.legend()
        plt.tight_layout()

        # Save comparison plot
        output_path = os.path.join(output_dir or OUTPUT_DIR, filename)
        plt.savefig(output_path)
        plt.close()
        print(f"Weight comparison visualization saved as {output_path}")


def export_budget_json(optimizer, filename, output_dir=OUTPUT_DIR):
    """Export optimal channel weights and month-by-month allocations as a JSON payload
    (alongside the PNGs) so the frontend can render interactive Plotly/Recharts charts."""
    if optimizer.results_df is None or optimizer.optimal_weights is None:
        print("Error: Nothing to export. Run optimize() first.")
        return

    weights = [
        {
            "channel": channel,
            "raw_weight": float(optimizer.optimal_weights[i]),
            "normalized_weight": float(optimizer.normalized_weights[i]),
            "weight_range": [float(v) for v in optimizer.weight_ranges.get(channel, (None, None))],
        }
        for i, channel in enumerate(optimizer.existing_channels)
    ]

    time_series = []
    for _, row in optimizer.results_df.iterrows():
        time_series.append({
            "month": row["Month"],
            "total_investment": float(row["Total_Investment"]),
            "projected_revenue": float(row["Projected_Revenue"]),
            "channels": {
                channel: {
                    "allocation": float(row[f"{channel}_Allocation"]),
                    "percentage": float(row[f"{channel}_Percentage"]),
                }
                for channel in optimizer.existing_channels
            },
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": type(optimizer).__name__,
        "channels": optimizer.existing_channels,
        "weights": weights,
        "time_series": time_series,
    }

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Budget allocation JSON exported to {output_path}")
