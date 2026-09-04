import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import os


class DataLoader:
    """Class to load and preprocess data"""
    
    def __init__(self, file_path):
        """Initialize the DataLoader with the file path"""
        self.file_path = file_path
        self.data = None
        
    def load_data(self):
        """Load data from CSV file"""
        print(f"Loading data from {self.file_path}...")
        self.data = pd.read_csv(self.file_path, low_memory=False)
        print(f"Data loaded. Shape: {self.data.shape}")
        return self.data
    
    def preprocess_data(self):
        """Preprocess the data"""
        if self.data is None:
            self.load_data()
            
        # Convert order_date to datetime
        if 'order_date' in self.data.columns:
            if not pd.api.types.is_datetime64_any_dtype(self.data['order_date']):
                self.data['order_date'] = pd.to_datetime(self.data['order_date'])
                
        # Add derived columns for analysis
        if 'order_date' in self.data.columns:
            self.data['month'] = self.data['order_date'].dt.strftime('%Y-%m')
            self.data['week'] = self.data['order_date'].dt.to_period('W').astype(str)
            
        return self.data


class RevenueAnalysis:
    """Class for analyzing revenue trends and patterns"""
    
    def __init__(self, data):
        """Initialize with dataframe"""
        self.data = data
        
    def analyze_daily_revenue(self):
        """Analyze daily revenue trends"""
        if 'gmv' in self.data.columns and 'order_date' in self.data.columns:
            # Create a time series of daily revenue
            daily_revenue = self.data.groupby(self.data['order_date'].dt.date)['gmv'].sum().reset_index()
            daily_revenue.columns = ['date', 'revenue']
            daily_revenue['date'] = pd.to_datetime(daily_revenue['date'])
            daily_revenue = daily_revenue.sort_values('date')
            daily_revenue_indexed = daily_revenue.set_index('date')
            
            return daily_revenue_indexed
        else:
            print("Required columns (gmv, order_date) not found in the dataframe.")
            return None
    
    def analyze_monthly_revenue(self):
        """Analyze monthly revenue trends"""
        if 'gmv' in self.data.columns and 'order_date' in self.data.columns:
            # Monthly aggregation to see seasonal patterns
            monthly_revenue = self.data.groupby(self.data['order_date'].dt.to_period('M'))['gmv'].sum().reset_index()
            monthly_revenue['order_date'] = monthly_revenue['order_date'].dt.to_timestamp()
            monthly_revenue.columns = ['month', 'revenue']
            
            return monthly_revenue
        else:
            print("Required columns (gmv, order_date) not found in the dataframe.")
            return None
    
    def analyze_seasonal_decomposition(self, period=7):
        """Perform time series decomposition"""
        daily_revenue = self.analyze_daily_revenue()
        
        if daily_revenue is not None and len(daily_revenue) > period * 2:
            try:
                # Perform decomposition
                decomposition = seasonal_decompose(daily_revenue['revenue'], model='additive', period=period)
                return decomposition
            except Exception as e:
                print(f"Could not perform time series decomposition: {e}")
                print("This might be due to missing values or insufficient data points.")
                return None
        else:
            print("Not enough data points for time series decomposition.")
            return None


class HolidayImpactAnalysis:
    """Class for analyzing impact of holidays on revenue"""
    
    def __init__(self, data):
        """Initialize with dataframe"""
        self.data = data
        
    def analyze_weekly_holiday_impact(self):
        """Analyze weekly holiday impact on revenue"""
        if all(col in self.data.columns for col in ['gmv', 'is_holiday', 'week']):
            # Weekly Analysis
            weekly_holiday_impact = self.data.groupby(['week', 'is_holiday']).agg({
                'gmv': ['sum', 'mean'],
                'order_id': 'count'
            }).reset_index()
            
            # Flatten column names
            weekly_holiday_impact.columns = ['week', 'is_holiday', 'total_gmv', 'avg_daily_gmv', 'order_count']
            weekly_holiday_impact['avg_order_value'] = weekly_holiday_impact['total_gmv'] / weekly_holiday_impact['order_count']
            
            # Calculate percentage of revenue from holiday vs non-holiday
            weekly_total = weekly_holiday_impact.groupby('week')['total_gmv'].sum().reset_index()
            weekly_total.rename(columns={'total_gmv': 'week_total_gmv'}, inplace=True)
            weekly_holiday_impact = weekly_holiday_impact.merge(weekly_total, on='week')
            weekly_holiday_impact['percentage'] = (weekly_holiday_impact['total_gmv'] / weekly_holiday_impact['week_total_gmv'] * 100).round(2)
            
            return weekly_holiday_impact
        else:
            print("Required columns (gmv, is_holiday, week) not found in the dataframe.")
            return None
    
    def analyze_monthly_holiday_impact(self):
        """Analyze monthly holiday impact on revenue"""
        if all(col in self.data.columns for col in ['gmv', 'is_holiday', 'month']):
            # Monthly Analysis
            monthly_holiday_impact = self.data.groupby(['month', 'is_holiday']).agg({
                'gmv': ['sum', 'mean'],
                'order_id': 'count'
            }).reset_index()
            
            # Flatten column names
            monthly_holiday_impact.columns = ['month', 'is_holiday', 'total_gmv', 'avg_daily_gmv', 'order_count']
            monthly_holiday_impact['avg_order_value'] = monthly_holiday_impact['total_gmv'] / monthly_holiday_impact['order_count']
            
            # Calculate percentage of revenue from holiday vs non-holiday
            monthly_total = monthly_holiday_impact.groupby('month')['total_gmv'].sum().reset_index()
            monthly_total.rename(columns={'total_gmv': 'month_total_gmv'}, inplace=True)
            monthly_holiday_impact = monthly_holiday_impact.merge(monthly_total, on='month')
            monthly_holiday_impact['percentage'] = (monthly_holiday_impact['total_gmv'] / monthly_holiday_impact['month_total_gmv'] * 100).round(2)
            
            return monthly_holiday_impact
        else:
            print("Required columns (gmv, is_holiday, month) not found in the dataframe.")
            return None
    
    def perform_statistical_test(self):
        """Perform statistical test on holiday vs non-holiday revenue"""
        if all(col in self.data.columns for col in ['gmv', 'is_holiday']):
            holiday_revenue = self.data[self.data['is_holiday'] == 1]['gmv']
            non_holiday_revenue = self.data[self.data['is_holiday'] == 0]['gmv']
            
            if len(holiday_revenue) > 0 and len(non_holiday_revenue) > 0:
                # T-test to check if the difference is statistically significant
                t_stat, p_value = stats.ttest_ind(holiday_revenue, non_holiday_revenue, equal_var=False)
                
                # Calculate average daily revenue for holiday vs non-holiday
                avg_holiday_revenue = holiday_revenue.mean()
                avg_non_holiday_revenue = non_holiday_revenue.mean()
                
                return {
                    't_stat': t_stat,
                    'p_value': p_value,
                    'avg_holiday_revenue': avg_holiday_revenue,
                    'avg_non_holiday_revenue': avg_non_holiday_revenue,
                    'difference': avg_holiday_revenue - avg_non_holiday_revenue,
                    'percentage_difference': ((avg_holiday_revenue / avg_non_holiday_revenue) - 1) * 100
                }
            else:
                print("Not enough data to perform statistical analysis.")
                return None
        else:
            print("Required columns (gmv, is_holiday) not found in the dataframe.")
            return None


class ProductCategoryAnalysis:
    """Class for analyzing product categories"""
    
    def __init__(self, data):
        """Initialize with dataframe"""
        self.data = data
        
    def analyze_super_categories(self):
        """Analyze product super categories"""
        if 'product_analytic_super_category' in self.data.columns and 'gmv' in self.data.columns:
            super_cat_gmv = self.data.groupby('product_analytic_super_category')['gmv'].sum().reset_index()
            super_cat_gmv = super_cat_gmv.sort_values('gmv', ascending=False)
            return super_cat_gmv
        else:
            print("Required columns not found in the dataframe.")
            return None
    
    def analyze_categories(self, top_n=15):
        """Analyze product categories"""
        if 'product_analytic_category' in self.data.columns and 'gmv' in self.data.columns:
            cat_gmv = self.data.groupby('product_analytic_category')['gmv'].sum().reset_index()
            cat_gmv = cat_gmv.sort_values('gmv', ascending=False).head(top_n)
            return cat_gmv
        else:
            print("Required columns not found in the dataframe.")
            return None
    
    def analyze_sub_categories(self, top_n=15):
        """Analyze product sub-categories"""
        if 'product_analytic_sub_category' in self.data.columns and 'gmv' in self.data.columns:
            subcat_gmv = self.data.groupby('product_analytic_sub_category')['gmv'].sum().reset_index()
            subcat_gmv = subcat_gmv.sort_values('gmv', ascending=False).head(top_n)
            return subcat_gmv
        else:
            print("Required columns not found in the dataframe.")
            return None
    
    def analyze_price_ranges(self):
        """Analyze product price ranges"""
        if 'product_mrp' in self.data.columns and 'gmv' in self.data.columns:
            # Create price bins
            price_bins = [0, 500, 1000, 2000, 5000, 10000, 20000, 50000, float('inf')]
            price_labels = ['0-500', '501-1000', '1001-2000', '2001-5000', '5001-10000', '10001-20000', '20001-50000', '50000+']
            
            # Add price range column
            data_copy = self.data.copy()
            data_copy['price_range'] = pd.cut(data_copy['product_mrp'], bins=price_bins, labels=price_labels)
            
            # Group by price range and calculate total GMV
            price_gmv = data_copy.groupby('price_range')['gmv'].sum().reset_index()
            
            return price_gmv
        else:
            print("Required columns not found in the dataframe.")
            return None


class DiscountAnalysis:
    """Class for analyzing the relationship between discount and GMV"""
    
    def __init__(self, data):
        """Initialize with dataframe"""
        self.data = data
        self.discount_column = 'Discount'  # or 'discount' based on actual column name
        
    def calculate_statistics(self):
        """Calculate basic statistics for discount and GMV"""
        if self.discount_column in self.data.columns and 'gmv' in self.data.columns:
            discount_stats = self.data[self.discount_column].describe()
            gmv_stats = self.data['gmv'].describe()
            correlation = self.data[self.discount_column].corr(self.data['gmv'])
            
            return {
                'discount_stats': discount_stats,
                'gmv_stats': gmv_stats,
                'correlation': correlation
            }
        else:
            print(f"Required columns ({self.discount_column}, gmv) not found in the dataframe.")
            return None
    
    def analyze_discount_segments(self):
        """Analyze GMV by discount segments"""
        if self.discount_column in self.data.columns and 'gmv' in self.data.columns:
            # Create discount segments
            discount_bins = [0, 10, 20, 30, 40, 50, 100]
            discount_labels = ['0-10%', '11-20%', '21-30%', '31-40%', '41-50%', '51%+']
            
            # Assign discount segments
            data_copy = self.data.copy()
            data_copy['discount_segment'] = pd.cut(data_copy[self.discount_column], bins=discount_bins, labels=discount_labels)
            
            # Calculate average GMV by discount segment
            segment_gmv = data_copy.groupby('discount_segment')['gmv'].mean().reset_index()
            
            return segment_gmv
        else:
            print(f"Required columns ({self.discount_column}, gmv) not found in the dataframe.")
            return None
    
    def analyze_monthly_trends(self):
        """Analyze monthly discount and GMV trends"""
        if self.discount_column in self.data.columns and 'gmv' in self.data.columns:
            # Calculate monthly average discount and GMV
            monthly_data = self.data.groupby(self.data['order_date'].dt.to_period('M')).agg({self.discount_column: 'mean', 'gmv': 'sum'}).reset_index()
            monthly_data['order_date'] = monthly_data['order_date'].dt.to_timestamp()
            
            return monthly_data
        else:
            print(f"Required columns ({self.discount_column}, gmv) not found in the dataframe.")
            return None
    
    def perform_regression(self):
        """Perform linear regression on discount vs GMV"""
        if self.discount_column in self.data.columns and 'gmv' in self.data.columns:
            # Perform linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(self.data[self.discount_column], self.data['gmv'])
            
            return {
                'slope': slope,
                'intercept': intercept,
                'r_value': r_value,
                'r_squared': r_value**2,
                'p_value': p_value,
                'std_err': std_err
            }
        else:
            print(f"Required columns ({self.discount_column}, gmv) not found in the dataframe.")
            return None


class MarketingAnalysis:
    """Class for analyzing marketing channels and investments"""
    
    def __init__(self, data):
        """Initialize with dataframe"""
        self.data = data
        self.marketing_channels = ['TV', 'Digital', 'Sponsorship', 'Content Marketing',
                                  'Online marketing', ' Affiliates', 'SEM', 'Radio', 'Other']
        
    def analyze_channel_investments(self):
        """Analyze monthly investment by channel"""
        # Check if the required columns exist
        if all(channel in self.data.columns for channel in self.marketing_channels) and 'Month' in self.data.columns:
            # Calculate monthly investment by channel
            monthly_investment = self.data.groupby('Month')[self.marketing_channels].mean().round(2)
            return monthly_investment
        else:
            print("Required marketing channel columns not found in the dataframe.")
            return None
    
    def calculate_channel_correlation(self):
        """Calculate correlation between GMV and marketing channels"""
        # Check if the required columns exist
        if all(channel in self.data.columns for channel in self.marketing_channels) and 'gmv' in self.data.columns:
            # Calculate correlation matrix
            correlation_matrix = self.data[['gmv'] + self.marketing_channels].corr()
            return correlation_matrix
        else:
            print("Required columns not found in the dataframe.")
            return None


class DataVisualizer:
    """Class for visualizing data and creating plots"""
    
    @staticmethod
    def plot_daily_revenue(daily_revenue):
        """Plot daily revenue trend"""
        fig = px.line(
            daily_revenue,
            y='revenue',
            title='Daily Revenue Over Time',
            labels={'index': 'Date', 'revenue': 'Revenue (GMV)'}
        )
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Revenue (GMV)',
            template='plotly_white'
        )
        return fig
    
    @staticmethod
    def plot_monthly_revenue(monthly_revenue):
        """Plot monthly revenue trend"""
        fig = px.line(
            monthly_revenue,
            x='month',
            y='revenue',
            markers=True,
            title='Monthly Revenue - Seasonal Pattern',
            labels={'month': 'Month', 'revenue': 'Revenue (GMV)'}
        )
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Revenue (GMV)',
            template='plotly_white'
        )
        return fig
    
    @staticmethod
    def plot_decomposition(decomposition):
        """Plot time series decomposition"""
        fig = make_subplots(
            rows=4,
            cols=1,
            subplot_titles=('Observed', 'Trend', 'Seasonality', 'Residuals'),
            vertical_spacing=0.1
        )
        
        # Add traces for each component
        fig.add_trace(
            go.Scatter(x=decomposition.observed.index, y=decomposition.observed, mode='lines', name='Observed'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=decomposition.trend.index, y=decomposition.trend, mode='lines', name='Trend'),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, mode='lines', name='Seasonality'),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=decomposition.resid.index, y=decomposition.resid, mode='lines', name='Residuals'),
            row=4, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=900,
            title_text='Time Series Decomposition of Revenue',
            showlegend=False
        )
        
        # Update y-axis titles
        fig.update_yaxes(title_text='Revenue', row=1, col=1)
        fig.update_yaxes(title_text='Trend', row=2, col=1)
        fig.update_yaxes(title_text='Seasonality', row=3, col=1)
        fig.update_yaxes(title_text='Residuals', row=4, col=1)
        
        return fig
    
    @staticmethod
    def plot_holiday_impact_weekly(weekly_holiday_impact):
        """Plot weekly holiday impact"""
        weekly_holiday_impact['is_holiday_label'] = weekly_holiday_impact['is_holiday'].map({0: 'No', 1: 'Yes'})
        fig = px.bar(
            weekly_holiday_impact,
            x='week',
            y='total_gmv',
            color='is_holiday_label',
            title='Weekly Revenue by Holiday Status',
            labels={'week': 'Week', 'total_gmv': 'Revenue (GMV)', 'is_holiday_label': 'Is Holiday'},
            barmode='group'
        )
        fig.update_layout(
            xaxis_tickangle=-90,
            legend_title_text='Is Holiday'
        )
        return fig
    
    @staticmethod
    def plot_holiday_impact_monthly(monthly_holiday_impact):
        """Plot monthly holiday impact"""
        monthly_holiday_impact['is_holiday_label'] = monthly_holiday_impact['is_holiday'].map({0: 'No', 1: 'Yes'})
        fig = px.bar(
            monthly_holiday_impact,
            x='month',
            y='total_gmv',
            color='is_holiday_label',
            title='Monthly Revenue by Holiday Status',
            labels={'month': 'Month', 'total_gmv': 'Revenue (GMV)', 'is_holiday_label': 'Is Holiday'},
            barmode='group'
        )
        fig.update_layout(
            xaxis_tickangle=-90,
            legend_title_text='Is Holiday'
        )
        return fig
    
    @staticmethod
    def plot_holiday_comparison(stats):
        """Plot holiday vs non-holiday comparison"""
        comparison_data = pd.DataFrame({
            'Period': ['Holiday', 'Non-Holiday'],
            'Average Revenue': [stats['avg_holiday_revenue'], stats['avg_non_holiday_revenue']]
        })
        
        fig = px.bar(
            comparison_data,
            x='Period',
            y='Average Revenue',
            title='Average Revenue: Holiday vs Non-Holiday',
            color='Period',
            text_auto='.2f'
        )
        fig.update_traces(textposition='outside')
        return fig
    
    @staticmethod
    def plot_super_categories(super_cat_gmv):
        """Plot GMV by super category"""
        fig = px.bar(
            super_cat_gmv,
            x='product_analytic_super_category',
            y='gmv',
            title='Total GMV by Product Super Category',
            labels={'product_analytic_super_category': 'Product Super Category', 'gmv': 'GMV'},
            color='gmv',
            color_continuous_scale='Viridis',
            text='gmv'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600,
            template='plotly_white'
        )
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        return fig
    
    @staticmethod
    def plot_categories(cat_gmv):
        """Plot GMV by category"""
        fig = px.bar(
            cat_gmv,
            x='product_analytic_category',
            y='gmv',
            title='Total GMV by Product Category (Top 15)',
            labels={'product_analytic_category': 'Product Category', 'gmv': 'GMV'},
            color='gmv',
            color_continuous_scale='Viridis',
            text='gmv'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600,
            template='plotly_white'
        )
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        return fig
    
    @staticmethod
    def plot_discount_segments(segment_gmv):
        """Plot GMV by discount segment"""
        fig = px.bar(
            segment_gmv,
            x='discount_segment',
            y='gmv',
            title='Average GMV by Discount Segment',
            labels={'discount_segment': 'Discount Range', 'gmv': 'Average GMV'},
            color='gmv',
            text='gmv'
        )
        fig.update_layout(template='plotly_white')
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        return fig
    
    @staticmethod
    def plot_discount_trend(monthly_data, discount_column='Discount'):
        """Plot monthly discount and GMV trend"""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add discount line
        fig.add_trace(
            go.Scatter(
                x=monthly_data['order_date'],
                y=monthly_data[discount_column],
                name="Average Discount",
                mode='lines+markers',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False,
        )
        
        # Add GMV line
        fig.add_trace(
            go.Scatter(
                x=monthly_data['order_date'],
                y=monthly_data['gmv'],
                name="Total GMV",
                mode='lines+markers',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ),
            secondary_y=True,
        )
        
        # Set titles
        fig.update_layout(
            title_text="Monthly Average Discount and Total GMV",
            template='plotly_white',
            xaxis=dict(tickangle=-45)
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Average Discount (%)", secondary_y=False)
        fig.update_yaxes(title_text="Total GMV", secondary_y=True)
        
        return fig
    
    @staticmethod
    def plot_marketing_investments(monthly_investment):
        """Plot monthly marketing investments"""
        fig = px.area(
            monthly_investment,
            x=monthly_investment.index,
            y=monthly_investment.columns,
            title='Monthly Investment Trends by Marketing Channel',
            labels={'value': 'Investment Amount', 'variable': 'Channel'},
            template='plotly_white'
        )
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Investment Amount'
        )
        return fig
    
    @staticmethod
    def plot_correlation_heatmap(correlation_matrix):
        """Plot correlation heatmap"""
        # Convert the matplotlib heatmap to a Plotly heatmap
        fig = px.imshow(
            correlation_matrix,
            text_auto='.3f',
            aspect="auto",
            color_continuous_scale='RdBu_r',
            origin='lower',
            title='Correlation Heatmap: Revenue vs Marketing Channels'
        )
        
        fig.update_layout(
            height=800,
            width=1000,
            xaxis_title="Variables",
            yaxis_title="Variables",
            template='plotly_white'
        )
        
        return fig


class RunAnalysis:
    """Class for running all analyses and saving plots to a specified directory"""
    
    def __init__(self, data, output_dir="Graphs_Master"):
        """Initialize with dataframe and output directory"""
        self.data = data
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
        
        # Initialize all analysis classes
        self.revenue_analysis = RevenueAnalysis(data)
        self.holiday_analysis = HolidayImpactAnalysis(data)
        self.product_analysis = ProductCategoryAnalysis(data)
        self.discount_analysis = DiscountAnalysis(data)
        self.marketing_analysis = MarketingAnalysis(data)
        
        # Initialize visualizer
        self.visualizer = DataVisualizer()
    
    def run_revenue_analysis(self):
        """Run revenue analysis and save plots"""
        print("\n=== Revenue Analysis ===")
        daily_revenue = self.revenue_analysis.analyze_daily_revenue()
        monthly_revenue = self.revenue_analysis.analyze_monthly_revenue()
        decomposition = self.revenue_analysis.analyze_seasonal_decomposition()
        
        if daily_revenue is not None:
            fig_daily = self.visualizer.plot_daily_revenue(daily_revenue)
            # Display the plot
            fig_daily.show()
            # Save the plot
            fig_daily.write_image(f"{self.output_dir}/daily_revenue_trend.png")
            print(f"Saved daily revenue trend plot to {self.output_dir}/daily_revenue_trend.png")
        
        if monthly_revenue is not None:
            fig_monthly = self.visualizer.plot_monthly_revenue(monthly_revenue)
            # Display the plot
            fig_monthly.show()
            # Save the plot
            fig_monthly.write_image(f"{self.output_dir}/monthly_revenue_trend.png")
            print(f"Saved monthly revenue trend plot to {self.output_dir}/monthly_revenue_trend.png")
        
        if decomposition is not None:
            fig_decomp = self.visualizer.plot_decomposition(decomposition)
            # Display the plot
            fig_decomp.show()
            # Save the plot
            fig_decomp.write_image(f"{self.output_dir}/revenue_decomposition.png")
            print(f"Saved revenue decomposition plot to {self.output_dir}/revenue_decomposition.png")
    
    def run_holiday_impact_analysis(self):
        """Run holiday impact analysis and save plots"""
        print("\n=== Holiday Impact Analysis ===")
        weekly_holiday_impact = self.holiday_analysis.analyze_weekly_holiday_impact()
        monthly_holiday_impact = self.holiday_analysis.analyze_monthly_holiday_impact()
        holiday_stats = self.holiday_analysis.perform_statistical_test()
        
        if weekly_holiday_impact is not None:
            print("\nWeekly Holiday Analysis:")
            print(weekly_holiday_impact.sort_values(['week', 'is_holiday']))
            fig_weekly = self.visualizer.plot_holiday_impact_weekly(weekly_holiday_impact)
            # Display the plot
            fig_weekly.show()
            # Save the plot
            fig_weekly.write_image(f"{self.output_dir}/weekly_holiday_impact.png")
            print(f"Saved weekly holiday impact plot to {self.output_dir}/weekly_holiday_impact.png")
        
        if monthly_holiday_impact is not None:
            print("\nMonthly Holiday Analysis:")
            for month in monthly_holiday_impact['month'].unique():
                month_data = monthly_holiday_impact[monthly_holiday_impact['month'] == month]
                print(f"\nMonth: {month}")
                for _, row in month_data.iterrows():
                    holiday_status = "Holiday" if row['is_holiday'] == 1 else "Non-Holiday"
                    print(f"{holiday_status}:")
                    print(f"Total Revenue: {row['total_gmv']:,.2f}")
                    print(f"Average Daily Revenue: {row['avg_daily_gmv']:,.2f}")
                    print(f"Average Order Value: {row['avg_order_value']:,.2f}")
                    print(f"Total Orders: {row['order_count']:,}")
                    print(f"Revenue Percentage: {row['percentage']}%")
            
            fig_monthly = self.visualizer.plot_holiday_impact_monthly(monthly_holiday_impact)
            # Display the plot
            fig_monthly.show()
            # Save the plot
            fig_monthly.write_image(f"{self.output_dir}/monthly_holiday_impact.png")
            print(f"Saved monthly holiday impact plot to {self.output_dir}/monthly_holiday_impact.png")
        
        if holiday_stats is not None:
            print("\nStatistical Analysis of Holiday Impact:")
            print(f"T-statistic: {holiday_stats['t_stat']:.4f}")
            print(f"P-value: {holiday_stats['p_value']:.4f}")
            
            if holiday_stats['p_value'] < 0.05:
                print("The difference in revenue between holiday and non-holiday periods is statistically significant.")
            else:
                print("The difference in revenue between holiday and non-holiday periods is not statistically significant.")
            
            print(f"Average Revenue on Holidays: {holiday_stats['avg_holiday_revenue']:.2f}")
            print(f"Average Revenue on Non-Holidays: {holiday_stats['avg_non_holiday_revenue']:.2f}")
            print(f"Difference: {holiday_stats['difference']:.2f}")
            print(f"Percentage Difference: {holiday_stats['percentage_difference']:.2f}%")
            
            fig_comparison = self.visualizer.plot_holiday_comparison(holiday_stats)
            # Display the plot
            fig_comparison.show()
            # Save the plot
            fig_comparison.write_image(f"{self.output_dir}/holiday_comparison.png")
            print(f"Saved holiday comparison plot to {self.output_dir}/holiday_comparison.png")
    
    def run_product_category_analysis(self):
        """Run product category analysis and save plots"""
        print("\n=== Product Category Analysis ===")
        super_cat_gmv = self.product_analysis.analyze_super_categories()
        cat_gmv = self.product_analysis.analyze_categories()
        subcat_gmv = self.product_analysis.analyze_sub_categories()
        price_gmv = self.product_analysis.analyze_price_ranges()
        
        if super_cat_gmv is not None:
            fig_super = self.visualizer.plot_super_categories(super_cat_gmv)
            # Display the plot
            fig_super.show()
            # Save the plot
            fig_super.write_image(f"{self.output_dir}/super_categories.png")
            print(f"Saved super categories plot to {self.output_dir}/super_categories.png")
        
        if cat_gmv is not None:
            fig_cat = self.visualizer.plot_categories(cat_gmv)
            # Display the plot
            fig_cat.show()
            # Save the plot
            fig_cat.write_image(f"{self.output_dir}/categories.png")
            print(f"Saved categories plot to {self.output_dir}/categories.png")
    
    def run_discount_analysis(self):
        """Run discount analysis and save plots"""
        print("\n=== Discount Analysis ===")
        discount_stats = self.discount_analysis.calculate_statistics()
        segment_gmv = self.discount_analysis.analyze_discount_segments()
        monthly_discount = self.discount_analysis.analyze_monthly_trends()
        regression_results = self.discount_analysis.perform_regression()
        
        if discount_stats is not None:
            print("Discount Statistics:")
            print(discount_stats['discount_stats'])
            print("\nGMV Statistics:")
            print(discount_stats['gmv_stats'])
            print(f"\nCorrelation between Discount and GMV: {discount_stats['correlation']:.4f}")
        
        if segment_gmv is not None:
            fig_segment = self.visualizer.plot_discount_segments(segment_gmv)
            # Display the plot
            fig_segment.show()
            # Save the plot
            fig_segment.write_image(f"{self.output_dir}/discount_segments.png")
            print(f"Saved discount segments plot to {self.output_dir}/discount_segments.png")
        
        if monthly_discount is not None:
            fig_discount = self.visualizer.plot_discount_trend(monthly_discount)
            # Display the plot
            fig_discount.show()
            # Save the plot
            fig_discount.write_image(f"{self.output_dir}/discount_trend.png")
            print(f"Saved discount trend plot to {self.output_dir}/discount_trend.png")
        
        if regression_results is not None:
            print("\nRegression Results:")
            print(f"Regression equation: GMV = {regression_results['slope']:.2f} * Discount + {regression_results['intercept']:.2f}")
            print(f"R-squared: {regression_results['r_squared']:.4f}")
            print(f"P-value: {regression_results['p_value']:.4f}")
            print(f"Standard error: {regression_results['std_err']:.4f}")
    
    def run_marketing_analysis(self):
        """Run marketing analysis and save plots"""
        print("\n=== Marketing Channel Analysis ===")
        monthly_investment = self.marketing_analysis.analyze_channel_investments()
        correlation_matrix = self.marketing_analysis.calculate_channel_correlation()
        
        if monthly_investment is not None:
            fig_investment = self.visualizer.plot_marketing_investments(monthly_investment)
            # Display the plot
            fig_investment.show()
            # Save the plot
            fig_investment.write_image(f"{self.output_dir}/marketing_investments.png")
            print(f"Saved marketing investments plot to {self.output_dir}/marketing_investments.png")
        
        if correlation_matrix is not None:
            fig_heatmap = self.visualizer.plot_correlation_heatmap(correlation_matrix)
            # Display the plot
            fig_heatmap.show()
            # Save the plot
            fig_heatmap.write_image(f"{self.output_dir}/marketing_correlation_heatmap.png")
            print(f"Saved marketing correlation heatmap to {self.output_dir}/marketing_correlation_heatmap.png")
    
    def run_all_analyses(self):
        """Run all analyses"""
        self.run_revenue_analysis()
        self.run_holiday_impact_analysis()
        self.run_product_category_analysis()
        self.run_discount_analysis()
        self.run_marketing_analysis()
        print(f"\nAll analyses completed. Plots saved to {self.output_dir}/ directory.")


def main():
    """Main function to run all analyses"""
    
    # Get CSV file path from user
    csv_path = input("Enter the path to your CSV file: ")
    
    # Initialize data loader and load data
    data_loader = DataLoader(csv_path)
    data = data_loader.load_data()
    data = data_loader.preprocess_data()
    
    # Create an instance of RunAnalysis and run all analyses
    analyzer = RunAnalysis(data)
    analyzer.run_all_analyses()


if __name__ == "__main__":
    main() 