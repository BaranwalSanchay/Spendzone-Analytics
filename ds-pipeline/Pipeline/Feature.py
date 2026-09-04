import pandas as pd
import os
from datetime import datetime


class DataLoader:
    """Class for loading and preprocessing data from CSV files"""
    
    def __init__(self, filepath):
        """Initialize with the path to the CSV file"""
        self.filepath = filepath
        self.data = None
    
    def load_data(self):
        """Load data from CSV file"""
        print(f"Loading data from {self.filepath}...")
        try:
            self.data = pd.read_csv(self.filepath)
            print(f"Successfully loaded data with {len(self.data)} rows and {len(self.data.columns)} columns.")
            return self.data
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return None


class FeatureEngineer:
    """Class for creating new features from the loaded dataset"""
    
    def __init__(self, dataframe):
        """Initialize with the input DataFrame"""
        self.df = dataframe.copy()
        
    def engineer_features(self):
        """Apply feature engineering to create new metrics"""
        print("Starting feature engineering...")
        
        # Convert order_date to datetime
        self.df['order_date'] = pd.to_datetime(self.df['order_date'])
        
        # Create day, week and month features
        print("Creating date-based features...")
        self.df['day'] = self.df['order_date'].dt.date
        self.df['week'] = self.df['order_date'].dt.to_period('W').astype(str)
        self.df['month'] = self.df['order_date'].dt.to_period('M').astype(str)
        
        # Create daily average order value
        print("Creating daily average order value...")
        self._add_daily_avg_order_value()
        
        # Create weekly average order value
        print("Creating weekly average order value...")
        self._add_weekly_avg_order_value()
        
        # Create monthly average order value
        print("Creating monthly average order value...")
        self._add_monthly_avg_order_value()
        
        # Create monthly revenue per customer
        print("Creating monthly revenue per customer...")
        self._add_monthly_revenue_per_customer()
        
        # Create weekly revenue per customer
        print("Creating weekly revenue per customer...")
        self._add_weekly_revenue_per_customer()
        
        print("Feature engineering completed.")
        return self.df
    
    def _add_daily_avg_order_value(self):
        """Calculate average order value per day"""
        # Total Revenue (sum of gmv) / Total Number of Orders (count of unique order_id)
        daily_revenue = self.df.groupby('day')['gmv'].sum()
        daily_orders = self.df.groupby('day')['order_id'].nunique()
        daily_avg_order_value = daily_revenue / daily_orders
        
        # Convert to DataFrame and reset index
        daily_avg_order_value = daily_avg_order_value.reset_index()
        daily_avg_order_value.columns = ['day', 'avg_order_value_daily']
        
        # Merge back with original dataframe
        self.df = self.df.merge(daily_avg_order_value, on='day', how='left')
    
    def _add_weekly_avg_order_value(self):
        """Calculate average order value per week"""
        # Total Revenue (sum of gmv) / Total Number of Orders (count of unique order_id)
        weekly_revenue = self.df.groupby('week')['gmv'].sum()
        weekly_orders = self.df.groupby('week')['order_id'].nunique()
        weekly_avg_order_value = weekly_revenue / weekly_orders
        
        # Convert to DataFrame and reset index
        weekly_avg_order_value = weekly_avg_order_value.reset_index()
        weekly_avg_order_value.columns = ['week', 'avg_order_value_weekly']
        
        # Merge back with original dataframe
        self.df = self.df.merge(weekly_avg_order_value, on='week', how='left')
    
    def _add_monthly_avg_order_value(self):
        """Calculate average order value per month"""
        # Total Revenue (sum of gmv) / Total Number of Orders (count of unique order_id)
        monthly_revenue = self.df.groupby('month')['gmv'].sum()
        monthly_orders = self.df.groupby('month')['order_id'].nunique()
        monthly_avg_order_value = monthly_revenue / monthly_orders
        
        # Convert to DataFrame and reset index
        monthly_avg_order_value = monthly_avg_order_value.reset_index()
        monthly_avg_order_value.columns = ['month', 'avg_order_value_monthly']
        
        # Merge back with original dataframe
        self.df = self.df.merge(monthly_avg_order_value, on='month', how='left')
    
    def _add_monthly_revenue_per_customer(self):
        """Calculate revenue per customer per month"""
        # Total Revenue (sum of gmv) / Total Number of Customers (count of unique cust_id)
        monthly_revenue = self.df.groupby('month')['gmv'].sum()
        monthly_customers = self.df.groupby('month')['cust_id'].nunique()
        monthly_revenue_per_customer = monthly_revenue / monthly_customers
        
        # Convert to DataFrame and reset index
        monthly_revenue_per_customer = monthly_revenue_per_customer.reset_index()
        monthly_revenue_per_customer.columns = ['month', 'revenue_per_customer_monthly']
        
        # Merge back with original dataframe
        self.df = self.df.merge(monthly_revenue_per_customer, on='month', how='left')
    
    def _add_weekly_revenue_per_customer(self):
        """Calculate revenue per customer per week"""
        # Total Revenue (sum of gmv) / Total Number of Customers (count of unique cust_id)
        weekly_revenue = self.df.groupby('week')['gmv'].sum()
        weekly_customers = self.df.groupby('week')['cust_id'].nunique()
        weekly_revenue_per_customer = weekly_revenue / weekly_customers
        
        # Convert to DataFrame and reset index
        weekly_revenue_per_customer = weekly_revenue_per_customer.reset_index()
        weekly_revenue_per_customer.columns = ['week', 'revenue_per_customer_weekly']
        
        # Merge back with original dataframe
        self.df = self.df.merge(weekly_revenue_per_customer, on='week', how='left')


class FeatureEngineeringOrchestrator:
    """Class to orchestrate the feature engineering process"""
    
    def __init__(self, input_filepath=None):
        """Initialize with input file path"""
        self.input_filepath = input_filepath
        self.output_filepath = None
        self.data = None
        self.engineered_data = None
        
    def set_input_filepath(self, filepath):
        """Set the input file path"""
        self.input_filepath = filepath
        
    def run_process(self):
        """Run the complete feature engineering process"""
        if not self.input_filepath:
            print("Error: No input file specified.")
            return False
            
        # Create output filepath based on input filename
        base_filename = os.path.basename(self.input_filepath)
        filename_without_ext, ext = os.path.splitext(base_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_filepath = f"{filename_without_ext}_engineered_{timestamp}{ext}"
            
        # Load data
        loader = DataLoader(self.input_filepath)
        self.data = loader.load_data()
        if self.data is None:
            return False
            
        # Engineer features
        engineer = FeatureEngineer(self.data)
        self.engineered_data = engineer.engineer_features()
        
        # Save results
        return self.save_results()
        
    def save_results(self):
        """Save the engineered data to CSV"""
        if self.engineered_data is None:
            print("Error: No engineered data to save.")
            return False
            
        try:
            self.engineered_data.to_csv(self.output_filepath, index=False)
            print(f"Successfully saved engineered data to {self.output_filepath}")
            
            # Display sample of engineered features
            print("\nSample of engineered features:")
            features = ['day', 'order_id', 'gmv', 'avg_order_value_daily', 
                        'week', 'avg_order_value_weekly', 
                        'month', 'avg_order_value_monthly',
                        'cust_id', 'revenue_per_customer_monthly', 'revenue_per_customer_weekly']
            print(self.engineered_data[features].head())
            
            return True
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            return False


def main():
    """Main function to run the feature engineering process"""
    print("===== Order Data Feature Engineering =====")
    print("This tool will create advanced metrics from your order data.")
    
    # Get input file path from user
    input_filepath = input("Please enter the path to your CSV file: ")
    
    # Validate file exists
    if not os.path.exists(input_filepath):
        print(f"Error: File '{input_filepath}' not found.")
        return
        
    # Run the process
    orchestrator = FeatureEngineeringOrchestrator(input_filepath)
    success = orchestrator.run_process()
    
    if success:
        print("\nFeature engineering process completed successfully.")
    else:
        print("\nFeature engineering process failed.")


if __name__ == "__main__":
    main()

