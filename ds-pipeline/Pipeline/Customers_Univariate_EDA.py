import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
# Import kaleido for saving plotly figures as static images
import kaleido
# Import argparse for command line arguments
import argparse

# Read the CSV file - This will be replaced by user input

class DataCleaner:
    """
    A class dedicated to data cleaning operations.
    """
    
    def __init__(self, dataframe):
        """
        Initialize the DataCleaner class with a DataFrame.
        
        Parameters:
        -----------
        dataframe : pandas.DataFrame
            The input DataFrame to be cleaned
        """
        self.df = dataframe.copy()
    
    def clean_data(self):
        """
        Performs comprehensive data cleaning on the DataFrame:
        1. Converts blank spaces, 'N' , and empty strings to NaN
        2. Handles delivery days columns
        3. Converts GMV to numeric
        4. Converts order_date to datetime
        5. Drops rows with null values in critical columns
        
        Returns:
        --------
        pandas.DataFrame: Cleaned DataFrame
        """
        # Convert blank spaces to NaN across all columns
        self.df = self.df.apply(lambda x: x.replace(r'^\s*$', np.nan, regex=True))
        
        # Convert '\N' and empty strings to NaN
        self.df = self.df.replace([r'\N', '', ' '], np.nan)
        
        # Convert delivery days columns to numeric, filling NaN with 0
        self.df['deliverybdays'] = pd.to_numeric(self.df['deliverybdays'], errors='coerce').fillna(0)
        self.df['deliverycdays'] = pd.to_numeric(self.df['deliverycdays'], errors='coerce').fillna(0)
        
        # Convert gmv to numeric
        self.df['gmv'] = pd.to_numeric(self.df['gmv'], errors='coerce')
        
        # Convert order_date to datetime
        self.df['order_date'] = pd.to_datetime(self.df['order_date'])
        
        # Drop rows where critical columns are null
        self.df = self.df.dropna(subset=['gmv', 'cust_id', 'pincode'])
        
        return self.df

class CustomerAnalytics:
    """
    A class containing methods for analyzing customer orders data.
    """
    
    def __init__(self, dataframe):
        """
        Initialize the CustomerAnalytics class with a DataFrame.
        
        Parameters:
        -----------
        dataframe : pandas.DataFrame
            The input DataFrame containing customer orders data
        """
        self.df = dataframe.copy()
        self._prepare_time_features()
    
    def get_dataframe_info(self):
        """
        Returns basic information about the dataset.
        """
        return self.df.info()
    
    def _prepare_time_features(self):
        """
        Prepare time-based features from order_date.
        This is an internal method called during initialization.
        """
        # Extract month, day, and week information
        self.df['month'] = self.df['order_date'].dt.month
        self.df['day'] = self.df['order_date'].dt.day
        self.df['week'] = self.df['order_date'].dt.isocalendar().week
        self.df['month_name'] = self.df['order_date'].dt.month_name()
    
    def analyze_time_based_orders(self):
        """
        Comprehensive time-based analysis of orders including:
        1. Monthly order counts
        2. Daily order counts for each month
        3. Weekly order counts for each month
        
        Returns:
        --------
        dict: Dictionary containing all plotly figures
            - 'monthly': Monthly orders figure
            - 'daily': List of daily orders figures by month
            - 'weekly': List of weekly orders figures by month
        """
        results = {}
        
        # 1. Monthly order counts
        monthly_orders = self.df.groupby('month_name').size().reset_index(name='count')
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        monthly_orders['month_name'] = pd.Categorical(monthly_orders['month_name'],
                                                    categories=month_order,
                                                    ordered=True)
        monthly_orders = monthly_orders.sort_values('month_name')
        
        fig_monthly = px.bar(monthly_orders, x='month_name', y='count',
                           title='Order Count by Month',
                           labels={'month_name': 'Month', 'count': 'Number of Orders'})
        fig_monthly.update_layout(xaxis={'categoryorder':'array', 'categoryarray':month_order})
        results['monthly'] = fig_monthly
        
        # Get available months in the data
        available_months = sorted(self.df['month_name'].unique(),
                                key=lambda x: pd.to_datetime(x, format='%B').month)
        
        # 2. Daily order counts for each month
        daily_figures = []
        for month in available_months:
            month_data = self.df[self.df['month_name'] == month]
            daily_orders = month_data.groupby('day').size().reset_index(name='count')
            
            fig_daily = px.bar(daily_orders, x='day', y='count',
                             title=f'Daily Order Count for {month}',
                             labels={'day': 'Day of Month', 'count': 'Number of Orders'})
            fig_daily.update_xaxes(type='category')
            daily_figures.append(fig_daily)
        results['daily'] = daily_figures
        
        # 3. Weekly order counts for each month
        weekly_figures = []
        for month in available_months:
            month_data = self.df[self.df['month_name'] == month]
            weekly_orders = month_data.groupby('week').size().reset_index(name='count')
            
            fig_weekly = px.bar(weekly_orders, x='week', y='count',
                              title=f'Weekly Order Count for {month}',
                              labels={'week': 'Week Number', 'count': 'Number of Orders'})
            fig_weekly.update_xaxes(type='category')
            weekly_figures.append(fig_weekly)
        results['weekly'] = weekly_figures
        
        return results
    
    def analyze_gmv(self):
        """
        Comprehensive analysis of Gross Merchandise Value (GMV) including:
        1. Summary statistics table
        2. Distribution histogram
        3. Distribution histogram with log scale
        4. Box plot
        5. Box plot without outliers
        6. Violin plot
        
        Returns:
        --------
        dict: Dictionary containing all plotly figures
            - 'stats': Summary statistics table
            - 'histogram': Regular histogram
            - 'histogram_log': Histogram with log scale
            - 'boxplot': Regular boxplot
            - 'boxplot_filtered': Boxplot without outliers
            - 'violin': Violin plot
        """
        results = {}
        
        # 1. Summary Statistics Table
        gmv_stats = self.df['gmv'].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Statistic', 'Value'],
                       fill_color='paleturquoise',
                       align='left'),
            cells=dict(values=[gmv_stats.index, gmv_stats.values.round(2)],
                      fill_color='lavender',
                      align='left'))
        ])
        fig_stats.update_layout(title='Summary Statistics for GMV')
        results['stats'] = fig_stats
        
        # 2. Regular Histogram
        fig_hist = px.histogram(self.df, x='gmv',
                              title='Distribution of GMV',
                              labels={'gmv': 'Gross Merchandise Value'},
                              nbins=50)
        fig_hist.update_layout(bargap=0.1)
        results['histogram'] = fig_hist
        
        # 3. Histogram with Log Scale
        fig_hist_log = px.histogram(self.df, x='gmv',
                                  title='Distribution of GMV (Log Scale)',
                                  labels={'gmv': 'Gross Merchandise Value'},
                                  nbins=50,
                                  log_y=True)
        fig_hist_log.update_layout(bargap=0.1)
        results['histogram_log'] = fig_hist_log
        
        # 4. Box Plot
        fig_box = px.box(self.df, y='gmv',
                        title='Boxplot of GMV',
                        labels={'gmv': 'Gross Merchandise Value'})
        results['boxplot'] = fig_box
        
        # 5. Filtered Box Plot (without outliers)
        Q1 = self.df['gmv'].quantile(0.25)
        Q3 = self.df['gmv'].quantile(0.75)
        IQR = Q3 - Q1
        filtered_df = self.df[(self.df['gmv'] >= Q1 - 1.5 * IQR) & 
                             (self.df['gmv'] <= Q3 + 1.5 * IQR)]
        
        fig_box_filtered = px.box(filtered_df, y='gmv',
                                title='Boxplot of GMV (Without Extreme Outliers)',
                                labels={'gmv': 'Gross Merchandise Value'})
        results['boxplot_filtered'] = fig_box_filtered
        
        # 6. Violin Plot
        fig_violin = px.violin(self.df, y='gmv',
                             title='Violin Plot of GMV',
                             labels={'gmv': 'Gross Merchandise Value'},
                             box=True)
        results['violin'] = fig_violin
        
        return results
    
    def analyze_payment_types(self):
        """
        Analyze the distribution of order payment types using:
        1. Bar chart with percentage labels
        2. Donut chart with percentage labels
        
        Returns:
        --------
        dict: Dictionary containing plotly figures
            - 'bar': Bar chart of payment type distribution
            - 'pie': Donut chart of payment type distribution
        """
        results = {}
        
        # Calculate payment type distribution
        payment_type_counts = self.df['order_payment_type'].value_counts().reset_index()
        payment_type_counts.columns = ['Payment Type', 'Count']
        
        # Calculate percentages
        total_orders = payment_type_counts['Count'].sum()
        payment_type_counts['Percentage'] = (payment_type_counts['Count'] / total_orders * 100).round(2)
        
        # Create bar chart
        fig_payment = px.bar(payment_type_counts,
                           x='Payment Type',
                           y='Count',
                           text=payment_type_counts['Percentage'].apply(lambda x: f'{x}%'),
                           title='Distribution of Order Payment Types',
                           color='Payment Type',
                           labels={'Count': 'Number of Orders'})
        
        # Customize bar chart layout
        fig_payment.update_traces(textposition='outside')
        fig_payment.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        results['bar'] = fig_payment
        
        # Create donut chart
        fig_pie = px.pie(payment_type_counts,
                        values='Count',
                        names='Payment Type',
                        title='Distribution of Order Payment Types',
                        hole=0.4)  # Makes it a donut chart
        
        # Customize donut chart layout
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        results['pie'] = fig_pie
        
        return results
    
    def analyze_sla(self):
        """
        Comprehensive analysis of Service Level Agreements (SLA) including:
        1. Bar chart of SLA distribution with percentages
        2. Box plot of SLA values
        3. Filtered box plot (without outliers)
        4. Donut chart of top 5 SLA values
        
        Returns:
        --------
        dict: Dictionary containing plotly figures
            - 'bar': Bar chart of SLA distribution
            - 'boxplot': Regular boxplot
            - 'boxplot_filtered': Boxplot without outliers
            - 'pie': Donut chart of top 5 SLA values
        """
        results = {}
        
        # Calculate SLA distribution
        sla_counts = self.df['sla'].value_counts().reset_index()
        sla_counts.columns = ['SLA (days)', 'Count']
        sla_counts = sla_counts.sort_values('SLA (days)')
        
        # Calculate percentages
        total_orders = sla_counts['Count'].sum()
        sla_counts['Percentage'] = (sla_counts['Count'] / total_orders * 100).round(2)
        
        # 1. Create bar chart for SLA distribution
        fig_sla = px.bar(sla_counts,
                        x='SLA (days)',
                        y='Count',
                        text=sla_counts['Percentage'].apply(lambda x: f'{x}%' if x > 1 else ''),
                        title='Distribution of Service Level Agreements (SLA)',
                        color='SLA (days)',
                        labels={'Count': 'Number of Orders'})
        
        # Customize bar chart layout
        fig_sla.update_traces(textposition='outside')
        fig_sla.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        fig_sla.update_xaxes(type='category')
        results['bar'] = fig_sla
        
        # 2. Create regular boxplot
        fig_sla_box = px.box(self.df,
                           y='sla',
                           title='Boxplot of Service Level Agreements (SLA)',
                           labels={'sla': 'SLA (days)'})
        results['boxplot'] = fig_sla_box
        
        # 3. Create filtered boxplot (without outliers)
        Q1 = self.df['sla'].quantile(0.25)
        Q3 = self.df['sla'].quantile(0.75)
        IQR = Q3 - Q1
        filtered_df_sla = self.df[(self.df['sla'] >= Q1 - 1.5 * IQR) & 
                                 (self.df['sla'] <= Q3 + 1.5 * IQR)]
        
        fig_sla_box_filtered = px.box(filtered_df_sla,
                                    y='sla',
                                    title='Boxplot of SLA (Without Extreme Outliers)',
                                    labels={'sla': 'SLA (days)'})
        results['boxplot_filtered'] = fig_sla_box_filtered
        
        # 4. Create donut chart for top 5 SLA values
        top_sla = sla_counts.head(5)
        other_sla = pd.DataFrame({
            'SLA (days)': ['Other'],
            'Count': [sla_counts['Count'].sum() - top_sla['Count'].sum()],
            'Percentage': [100 - top_sla['Percentage'].sum()]
        })
        pie_data = pd.concat([top_sla, other_sla])
        
        fig_sla_pie = px.pie(pie_data,
                           values='Count',
                           names='SLA (days)',
                           title='Distribution of Top SLA Values',
                           hole=0.4)
        
        # Customize donut chart layout
        fig_sla_pie.update_traces(textposition='inside', textinfo='percent+label')
        results['pie'] = fig_sla_pie
        
        return results
    
    def analyze_product_mrp(self):
        """
        Comprehensive analysis of Product MRP (Maximum Retail Price) including:
        1. Summary statistics table
        2. Distribution histogram
        3. Distribution histogram with log scale
        4. Box plot
        5. Box plot without outliers
        6. Violin plot
        7. Price range distribution (bar chart)
        8. Price range distribution (donut chart)
        
        Returns:
        --------
        dict: Dictionary containing plotly figures
            - 'stats': Summary statistics table
            - 'histogram': Regular histogram
            - 'histogram_log': Histogram with log scale
            - 'boxplot': Regular boxplot
            - 'boxplot_filtered': Boxplot without outliers
            - 'violin': Violin plot
            - 'price_range_bar': Bar chart of price ranges
            - 'price_range_pie': Donut chart of price ranges
        """
        results = {}
        
        # 1. Summary Statistics Table
        mrp_stats = self.df['product_mrp'].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Statistic', 'Value'],
                       fill_color='paleturquoise',
                       align='left'),
            cells=dict(values=[mrp_stats.index, mrp_stats.values.round(2)],
                      fill_color='lavender',
                      align='left'))
        ])
        fig_stats.update_layout(title='Summary Statistics for Product MRP')
        results['stats'] = fig_stats
        
        # 2. Regular Histogram
        fig_hist = px.histogram(self.df, x='product_mrp',
                              title='Distribution of Product MRP',
                              labels={'product_mrp': 'Product MRP (₹)', 'count': 'Number of Orders'},
                              nbins=50)
        fig_hist.update_layout(bargap=0.1)
        results['histogram'] = fig_hist
        
        # 3. Histogram with Log Scale
        fig_hist_log = px.histogram(self.df, x='product_mrp',
                                  title='Distribution of Product MRP (Log Scale)',
                                  labels={'product_mrp': 'Product MRP (₹)', 'count': 'Number of Orders'},
                                  nbins=50,
                                  log_y=True)
        fig_hist_log.update_layout(bargap=0.1)
        results['histogram_log'] = fig_hist_log
        
        # 4. Box Plot
        fig_box = px.box(self.df, y='product_mrp',
                        title='Boxplot of Product MRP',
                        labels={'product_mrp': 'Product MRP (₹)'})
        results['boxplot'] = fig_box
        
        # 5. Filtered Box Plot (without outliers)
        Q1 = self.df['product_mrp'].quantile(0.25)
        Q3 = self.df['product_mrp'].quantile(0.75)
        IQR = Q3 - Q1
        filtered_df = self.df[(self.df['product_mrp'] >= Q1 - 1.5 * IQR) & 
                             (self.df['product_mrp'] <= Q3 + 1.5 * IQR)]
        
        fig_box_filtered = px.box(filtered_df, y='product_mrp',
                                title='Boxplot of Product MRP (Without Extreme Outliers)',
                                labels={'product_mrp': 'Product MRP (₹)'})
        results['boxplot_filtered'] = fig_box_filtered
        
        # 6. Violin Plot
        fig_violin = px.violin(self.df, y='product_mrp',
                             title='Violin Plot of Product MRP',
                             labels={'product_mrp': 'Product MRP (₹)'},
                             box=True)
        results['violin'] = fig_violin
        
        # Create price range categories
        price_bins = [0, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, self.df['product_mrp'].max()]
        price_labels = ['0-500', '501-1000', '1001-2000', '2001-5000', '5001-10000',
                       '10001-20000', '20001-50000', '50001-100000', '100000+']
        
        self.df['price_range'] = pd.cut(self.df['product_mrp'], bins=price_bins, labels=price_labels)
        
        # Calculate price range distribution
        price_range_counts = self.df['price_range'].value_counts().reset_index()
        price_range_counts.columns = ['Price Range', 'Count']
        price_range_counts = price_range_counts.sort_values('Price Range')
        
        # Calculate percentages
        total_products = price_range_counts['Count'].sum()
        price_range_counts['Percentage'] = (price_range_counts['Count'] / total_products * 100).round(2)
        
        # 7. Bar chart of price ranges
        fig_price_range = px.bar(price_range_counts,
                               x='Price Range',
                               y='Count',
                               text=price_range_counts['Percentage'].apply(lambda x: f'{x}%' if x > 1 else ''),
                               title='Distribution of Products by Price Range',
                               color='Price Range',
                               labels={'Count': 'Number of Orders'})
        
        fig_price_range.update_traces(textposition='outside')
        fig_price_range.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        results['price_range_bar'] = fig_price_range
        
        # 8. Donut chart of price ranges
        fig_price_pie = px.pie(price_range_counts,
                             values='Count',
                             names='Price Range',
                             title='Distribution of Products by Price Range',
                             hole=0.4)
        
        fig_price_pie.update_traces(textposition='inside', textinfo='percent+label')
        results['price_range_pie'] = fig_price_pie
        
        return results
    
    def analyze_pincodes(self):
        """
        Comprehensive analysis of order distribution by pincodes including:
        1. Histogram of pincode prefixes
        2. Bar chart of top 20 most frequent pincodes
        3. Donut chart of top 10 pincode prefixes
        
        Returns:
        --------
        dict: Dictionary containing plotly figures
            - 'prefix_histogram': Histogram of pincode prefixes
            - 'top_pincodes': Bar chart of top 20 pincodes
            - 'prefix_pie': Donut chart of top 10 prefixes
        """
        results = {}
        
        # Convert pincode to string and extract prefix
        self.df['pincode_str'] = self.df['pincode'].astype(str)
        self.df['pincode_prefix'] = self.df['pincode_str'].str[:2]  # First 2 digits
        
        # 1. Create histogram of pincodes by prefix
        fig_pincode_hist = px.histogram(self.df,
                                      x='pincode_prefix',
                                      title='Distribution of Orders by Pincode Prefix',
                                      labels={'pincode_prefix': 'Pincode Prefix', 
                                             'count': 'Number of Orders'},
                                      color_discrete_sequence=['#636EFA'])
        fig_pincode_hist.update_layout(bargap=0.1)
        results['prefix_histogram'] = fig_pincode_hist
        
        # 2. Create bar chart for top 20 pincodes
        pincode_counts = self.df['pincode'].value_counts().reset_index()
        pincode_counts.columns = ['Pincode', 'Count']
        top_pincodes = pincode_counts.head(20)
        
        fig_top_pincodes = px.bar(top_pincodes,
                                x='Pincode',
                                y='Count',
                                title='Top 20 Most Frequent Pincodes',
                                labels={'Pincode': 'Pincode', 
                                       'Count': 'Number of Orders'},
                                color='Count',
                                color_continuous_scale='Viridis')
        
        fig_top_pincodes.update_layout(xaxis_tickangle=-45)
        results['top_pincodes'] = fig_top_pincodes
        
        # 3. Create donut chart for top 10 pincode prefixes
        pincode_prefix_counts = self.df.groupby('pincode_prefix').size().reset_index(name='Count')
        pincode_prefix_counts = pincode_prefix_counts.sort_values('Count', ascending=False)
        top_10_prefixes = pincode_prefix_counts.head(10)
        
        fig_prefix_pie = px.pie(top_10_prefixes,
                              values='Count',
                              names='pincode_prefix',
                              title='Distribution of Orders by Top 10 Pincode Prefixes',
                              hole=0.4)
        
        fig_prefix_pie.update_traces(textposition='inside', textinfo='percent+label')
        results['prefix_pie'] = fig_prefix_pie
        
        return results
    
    def analyze_customer_behavior(self):
        """
        Comprehensive analysis of customer behavior including:
        1. Order frequency distribution
        2. Order frequency distribution (log scale)
        3. Customer spending distribution
        
        Returns:
        --------
        dict: Dictionary containing plotly figures
            - 'order_frequency': Bar chart of orders per customer
            - 'order_frequency_log': Log-scale bar chart of orders per customer
            - 'spending_distribution': Bar chart of customer spending ranges
        """
        results = {}
        
        # Convert customer ID to string for grouping
        self.df['cust_id_str'] = self.df['cust_id'].astype(str)
        
        # 1. Customer order frequency analysis
        customer_order_counts = self.df.groupby('cust_id').size().reset_index(name='order_count')
        order_frequency = customer_order_counts['order_count'].value_counts().reset_index()
        order_frequency.columns = ['Orders per Customer', 'Number of Customers']
        order_frequency = order_frequency.sort_values('Orders per Customer')
        
        # Regular bar chart of order frequency
        fig_order_freq = px.bar(order_frequency,
                              x='Orders per Customer',
                              y='Number of Customers',
                              title='Distribution of Orders per Customer',
                              labels={'Number of Customers': 'Count of Customers'},
                              color_discrete_sequence=['#636EFA'])
        fig_order_freq.update_layout(bargap=0.1)
        results['order_frequency'] = fig_order_freq
        
        # Log scale version
        fig_order_freq_log = px.bar(order_frequency,
                                  x='Orders per Customer',
                                  y='Number of Customers',
                                  title='Distribution of Orders per Customer (Log Scale)',
                                  labels={'Number of Customers': 'Count of Customers'},
                                  log_y=True)
        fig_order_freq_log.update_layout(bargap=0.1)
        results['order_frequency_log'] = fig_order_freq_log
        
        # 2. Customer spending analysis
        customer_spending = self.df.groupby('cust_id')['gmv'].sum().reset_index()
        customer_spending.columns = ['Customer ID', 'Total Spending']
        
        # Create spending ranges
        spending_bins = [0, 1000, 5000, 10000, 50000, 100000, float('inf')]
        spending_labels = ['0-1K', '1K-5K', '5K-10K', '10K-50K', '50K-100K', '100K+']
        customer_spending['Spending Range'] = pd.cut(customer_spending['Total Spending'],
                                                  bins=spending_bins,
                                                  labels=spending_labels)
        
        # Create bar chart of spending distribution
        spending_dist = customer_spending['Spending Range'].value_counts().reset_index()
        spending_dist.columns = ['Spending Range', 'Number of Customers']
        spending_dist = spending_dist.sort_values('Spending Range')
        
        fig_spending = px.bar(spending_dist,
                           x='Spending Range',
                           y='Number of Customers',
                           title='Distribution of Customer Spending',
                           color='Spending Range',
                           labels={'Number of Customers': 'Count of Customers'})
        results['spending_distribution'] = fig_spending
        
        return results
    
    def analyze_fsn(self):
        """
        Comprehensive analysis of FSN (Flipkart Stock Number) IDs including:
        1. Top 20 most frequent FSN IDs bar chart
        2. Distribution histogram of orders per FSN ID
        3. Log-scale distribution histogram
        4. Summary statistics table
        5. Box plot of GMV for top 10 FSN IDs
        
        Returns:
        --------
        dict: Dictionary containing plotly figures
            - 'top_20': Bar chart of top 20 FSN IDs
            - 'histogram': Distribution histogram
            - 'histogram_log': Log-scale histogram
            - 'stats': Summary statistics table
            - 'top_10_gmv': Box plot of GMV for top 10 FSN IDs
        """
        results = {}
        
        # Get FSN ID frequency distribution
        fsn_counts = self.df['fsn_id'].value_counts().reset_index()
        fsn_counts.columns = ['FSN ID', 'Count']
        
        # Calculate percentages
        total_items = fsn_counts['Count'].sum()
        fsn_counts['Percentage'] = (fsn_counts['Count'] / total_items * 100).round(2)
        
        # 1. Create bar chart for top 20 FSN IDs
        top_20_fsn = fsn_counts.head(20)
        fig_top_fsn = px.bar(top_20_fsn,
                           x='FSN ID',
                           y='Count',
                           title='Top 20 Most Frequent FSN IDs',
                           text=top_20_fsn['Percentage'].apply(lambda x: f'{x}%'),
                           color='Count',
                           labels={'Count': 'Number of Orders'})
        
        # Customize layout
        fig_top_fsn.update_traces(textposition='outside')
        fig_top_fsn.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            xaxis_title='FSN ID',
            yaxis_title='Number of Orders'
        )
        results['top_20'] = fig_top_fsn
        
        # 2. Create histogram of orders per FSN ID
        fig_hist = px.histogram(fsn_counts,
                              x='Count',
                              title='Distribution of Orders per FSN ID',
                              labels={'Count': 'Number of Orders', 'count': 'Number of FSN IDs'},
                              nbins=50)
        fig_hist.update_layout(bargap=0.1)
        results['histogram'] = fig_hist
        
        # 3. Create log scale histogram
        fig_hist_log = px.histogram(fsn_counts,
                                  x='Count',
                                  title='Distribution of Orders per FSN ID (Log Scale)',
                                  labels={'Count': 'Number of Orders', 'count': 'Number of FSN IDs'},
                                  log_y=True,
                                  nbins=50)
        fig_hist_log.update_layout(bargap=0.1)
        results['histogram_log'] = fig_hist_log
        
        # 4. Create summary statistics table
        fsn_stats = self.df.groupby('fsn_id').agg({
            'gmv': ['count', 'mean', 'sum'],
            'product_mrp': 'first',
            'product_procurement_sla': 'first'
        }).reset_index()
        
        fsn_stats.columns = ['FSN ID', 'Order Count', 'Average GMV', 'Total GMV', 'MRP', 'Procurement SLA']
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                       fill_color='paleturquoise',
                       align='left'),
            cells=dict(values=[
                ['Total Unique FSN IDs',
                 'Average Orders per FSN',
                 'Median Orders per FSN',
                 'Most Common FSN Orders',
                 'FSN IDs with Single Order (%)',
                 'Top 10% FSN IDs Account for (% orders)'],
                [len(fsn_counts),
                 fsn_counts['Count'].mean().round(2),
                 fsn_counts['Count'].median(),
                 fsn_counts['Count'].mode()[0],
                 (fsn_counts['Count'] == 1).mean() * 100,
                 fsn_counts.nlargest(int(len(fsn_counts)*0.1), 'Count')['Count'].sum() / total_items * 100]
            ],
            fill_color='lavender',
            align='left'))
        ])
        fig_stats.update_layout(title='FSN ID Distribution Statistics')
        results['stats'] = fig_stats
        
        # 5. Create box plot of GMV for top 10 FSN IDs
        top_10_fsn = fsn_counts.head(10)['FSN ID'].tolist()
        top_10_data = self.df[self.df['fsn_id'].isin(top_10_fsn)]
        
        fig_box = px.box(top_10_data,
                       x='fsn_id',
                       y='gmv',
                       title='GMV Distribution for Top 10 FSN IDs',
                       labels={'fsn_id': 'FSN ID', 'gmv': 'GMV'})
        fig_box.update_layout(xaxis_tickangle=-45)
        results['top_10_gmv'] = fig_box
        
        return results
    

class AnalyticsOrchestrator:
    """
    A class that orchestrates the execution of all analytics functions and manages their outputs.
    """
    
    def __init__(self, data_path):
        """
        Initialize the orchestrator with the path to the data file.
        
        Parameters:
        -----------
        data_path : str
            Path to the CSV file containing the data
        """
        self.data_path = data_path
        self.results = {}
        
    def run_all_analyses(self):
        """
        Run all available analyses and store their results.
        
        Returns:
        --------
        dict: Dictionary containing all analysis results
        """
        # Read and clean the data
        df = pd.read_csv(self.data_path)
        cleaner = DataCleaner(df)
        cleaned_data = cleaner.clean_data()
        
        # Initialize analytics
        analytics = CustomerAnalytics(cleaned_data)
        
        # Run all analyses and store results
        self.results['time_based'] = analytics.analyze_time_based_orders()
        self.results['gmv'] = analytics.analyze_gmv()
        self.results['payment'] = analytics.analyze_payment_types()
        self.results['sla'] = analytics.analyze_sla()
        self.results['product_mrp'] = analytics.analyze_product_mrp()
        self.results['pincodes'] = analytics.analyze_pincodes()
        self.results['customer_behavior'] = analytics.analyze_customer_behavior()
        self.results['fsn'] = analytics.analyze_fsn()
        
        return self.results
    
    def display_all_plots(self):
        """
        Display all plots from the analyses in an organized manner.
        """
        if not self.results:
            print("No results found. Please run analyze_all() first.")
            return
        
        # Define plot order and sections
        sections = {
            'Time-based Analysis': {
                'data': 'time_based',
                'plots': ['monthly', 'daily', 'weekly']
            },
            'GMV Analysis': {
                'data': 'gmv',
                'plots': ['stats', 'histogram', 'histogram_log', 'boxplot', 
                         'boxplot_filtered', 'violin']
            },
            'Payment Analysis': {
                'data': 'payment',
                'plots': ['bar', 'pie']
            },
            'SLA Analysis': {
                'data': 'sla',
                'plots': ['bar', 'boxplot', 'boxplot_filtered', 'pie']
            },
            'Product MRP Analysis': {
                'data': 'product_mrp',
                'plots': ['stats', 'histogram', 'histogram_log', 'boxplot',
                         'boxplot_filtered', 'violin', 'price_range_bar', 
                         'price_range_pie']
            },
            'Pincode Analysis': {
                'data': 'pincodes',
                'plots': ['prefix_histogram', 'top_pincodes', 'prefix_pie']
            },
            'Customer Behavior Analysis': {
                'data': 'customer_behavior',
                'plots': ['order_frequency', 'order_frequency_log', 
                         'spending_distribution']
            },
            'FSN Analysis': {
                'data': 'fsn',
                'plots': ['top_20', 'histogram', 'histogram_log', 'stats', 
                         'top_10_gmv']
            }
        }
        
        # Display plots section by section
        for section_name, section_info in sections.items():
            print(f"\n{'='*50}")
            print(f"{section_name:^50}")
            print(f"{'='*50}\n")
            
            data_key = section_info['data']
            if data_key in self.results:
                for plot_key in section_info['plots']:
                    if isinstance(self.results[data_key], dict):
                        plot = self.results[data_key].get(plot_key)
                        if plot:
                            if plot_key == 'daily' or plot_key == 'weekly':
                                # Handle lists of plots
                                for idx, p in enumerate(plot, 1):
                                    print(f"\n{plot_key.title()} Plot {idx}")
                                    p.show()
                            else:
                                print(f"\n{plot_key.title().replace('_', ' ')}")
                                plot.show()
                    else:
                        print(f"Warning: Results for {data_key} is not in expected format")
            else:
                print(f"Warning: No results found for {data_key}")
    
    def save_plots(self, output_dir='./Graphs_Uni'):
        """
        Save all plots from the analyses to the specified directory as PNG files.
        All plots are saved directly to the output directory without creating subfolders.
        
        Parameters:
        -----------
        output_dir : str
            Directory path where plots will be saved
        """
        if not self.results:
            print("No results found. Please run run_all_analyses() first.")
            return
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save all plots directly to the output directory
        saved_count = 0
        
        # Iterate through all results
        for analysis_key, analysis_data in self.results.items():
            # Skip non-dictionary results
            if not isinstance(analysis_data, dict):
                continue
                
            # For each plot in the analysis results
            for plot_key, plot in analysis_data.items():
                # Handle lists of plots (like daily and weekly in time_based)
                if isinstance(plot, list):
                    for idx, p in enumerate(plot):
                        if hasattr(p, 'write_image'):
                            file_path = os.path.join(output_dir, f"{analysis_key}_{plot_key}_{idx}.png")
                            try:
                                p.write_image(file_path, width=1200, height=800)
                                print(f"Saved {analysis_key}_{plot_key}_{idx} to {file_path}")
                                saved_count += 1
                            except Exception as e:
                                print(f"Error saving {analysis_key}_{plot_key}_{idx}: {e}")
                # Handle individual plots
                elif hasattr(plot, 'write_image'):
                    file_path = os.path.join(output_dir, f"{analysis_key}_{plot_key}.png")
                    try:
                        plot.write_image(file_path, width=1200, height=800)
                        print(f"Saved {analysis_key}_{plot_key} to {file_path}")
                        saved_count += 1
                    except Exception as e:
                        print(f"Error saving {analysis_key}_{plot_key}: {e}")
        
        print(f"\nAll plots saved to {output_dir}")
        print(f"Total plots saved: {saved_count}")

def main():
    """
    Main function to run all analyses and display results.
    """
    # Parse command line arguments for output directory only
    parser = argparse.ArgumentParser(description='Customer Data Analysis')
    parser.add_argument('--output', type=str, default='./Graphs_Uni', 
                        help='Directory to save output graphs (default: ./Graphs_Uni)')
    args = parser.parse_args()
    
    # Get CSV file path from user input
    csv_file = input("Enter the path to your CSV file: ")
    
    # Verify file exists
    while not os.path.isfile(csv_file):
        print(f"Error: File '{csv_file}' not found.")
        csv_file = input("Enter a valid path to your CSV file: ")
    
    # Initialize the orchestrator with the data file path from user input
    orchestrator = AnalyticsOrchestrator(csv_file)
    
    # Run all analyses
    print(f"Running all analyses on {csv_file}...")
    orchestrator.run_all_analyses()
    
    # Display all plots
    print("\nDisplaying all analysis results...")
    orchestrator.display_all_plots()
    
    # Always save plots without asking
    print(f"\nSaving all plots to {args.output}...")
    orchestrator.save_plots(args.output)

if __name__ == "__main__":
    main()