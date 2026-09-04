import numpy as np
import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class InvestmentAnalysis:
    def __init__(self, df):
        """Initialize with a DataFrame."""
        self.df = df.copy()
        self.categories = ['Camera', 'CameraAccessory', 'EntertainmentSmall', 'GameCDDVD', 'GamingHardware']

    def preprocess_data(self):
        """Preprocess the DataFrame."""
        self.df = self.df[:-3]  # Remove last 3 rows
        self.df.fillna(0, inplace=True)  # Fill NaN with 0
        for category in self.categories:
            self.df[f'{category}_investment_change'] = self.df[category].diff()

    def perform_wilcoxon_test(self):
        """Perform Wilcoxon signed-rank test for investment changes."""
        results = {}
        for category in self.categories:
            investment_change = self.df[f'{category}_investment_change'].dropna().values
            stat, p_value = stats.wilcoxon(investment_change)
            results[category] = {'Statistic': stat, 'P-Value': p_value}
        return results
    
    def perform_mannwhitneyu_test(self):
        """Perform Mann-Whitney U test for investment changes."""
        results = {}
        for category in self.categories:
            group1 = self.df[f'{category}_investment_change'].dropna().values[:len(self.df)//2]
            group2 = self.df[f'{category}_investment_change'].dropna().values[len(self.df)//2:]
            stat, p_value = stats.mannwhitneyu(group1, group2)
            results[category] = {'Statistic': stat, 'P-Value': p_value}
        return results
    
    def perform_kruskal_test(self):
        """Perform Kruskal-Wallis test across all categories."""
        data = [self.df[f'{category}_investment_change'].dropna().values for category in self.categories]
        stat, p_value = stats.kruskal(*data)
        return {'Statistic': stat, 'P-Value': p_value}
    
    def perform_spearman_correlation(self):
        """Compute Spearman correlation between categories."""
        correlation_matrix = self.df[self.categories].corr(method='spearman')
        return correlation_matrix
    
    def visualize_investment_changes(self):
        """Visualize investment changes using a boxplot."""
        plt.figure(figsize=(10, 5))
        sns.boxplot(data=self.df[[f'{category}_investment_change' for category in self.categories]])
        plt.xticks(rotation=45)
        plt.title("Investment Changes Distribution")
        plt.show()
        
    def run_analyzer(self):
        """Run all analyses and display results."""
        print("Preprocessing data...")
        self.preprocess_data()
        
        print("\n--- Wilcoxon Signed-Rank Test Results ---")
        wilcoxon_results = self.perform_wilcoxon_test()
        for category, result in wilcoxon_results.items():
            print(f"{category}: Statistic = {result['Statistic']:.4f}, P-Value = {result['P-Value']:.4f}")
        
        print("\n--- Mann-Whitney U Test Results ---")
        mannwhitneyu_results = self.perform_mannwhitneyu_test()
        for category, result in mannwhitneyu_results.items():
            print(f"{category}: Statistic = {result['Statistic']:.4f}, P-Value = {result['P-Value']:.4f}")
        
        print("\n--- Kruskal-Wallis Test Results ---")
        kruskal_results = self.perform_kruskal_test()
        print(f"Statistic = {kruskal_results['Statistic']:.4f}, P-Value = {kruskal_results['P-Value']:.4f}")
        
        print("\n--- Spearman Correlation Matrix ---")
        corr_matrix = self.perform_spearman_correlation()
        print(corr_matrix)
        
        print("\n--- Visualizing Investment Changes ---")
        self.visualize_investment_changes()

def main():
    """Main function to run the analysis."""
    try:
        # Use specific CSV file path
        csv_file = "CSV Input Files/month.csv"
        
        # Load data
        print(f"Loading data from {csv_file}...")
        df = pd.read_csv(csv_file)
        
        # Create analyzer and run analysis
        analyzer = InvestmentAnalysis(df)
        analyzer.run_analyzer()
        
    except FileNotFoundError:
        print(f"Error: File not found. Please check the file path and try again.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
