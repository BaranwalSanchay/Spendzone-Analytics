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

# Take CSV file path from user
csv_path = input("Enter the path to your CSV file: ")
df = pd.read_csv(csv_path)

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
        
        #Drop both delivery columns
        self.df = self.df.drop(['deliverybdays', 'deliverycdays'], axis=1)
        
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
    
    def analyze_sales_trends(self):
        """
        Comprehensive analysis of sales trends including:
        1. Daily GMV trend
        2. Daily Units Sold trend
        3. Monthly combined GMV and Units trend
        4. Weekly combined GMV and Units trend
        5. Sales statistics and insights
        
        Returns:
        --------
        dict: Dictionary containing plotly figures and statistics
        """
        results = {}
        
        # Create daily aggregations
        daily_sales = self.df.groupby('order_date').agg({
            'gmv': 'sum',
            'units': 'sum'
        }).reset_index()

        # Create monthly aggregations
        monthly_sales = self.df.groupby(self.df['order_date'].dt.to_period('M')).agg({
            'gmv': 'sum',
            'units': 'sum'
        }).reset_index()
        monthly_sales['order_date'] = monthly_sales['order_date'].astype(str)

        # Create weekly aggregations
        weekly_sales = self.df.groupby(self.df['order_date'].dt.isocalendar().week).agg({
            'gmv': 'sum',
            'units': 'sum'
        }).reset_index()

        # 1. Daily GMV Trend
        fig_daily_gmv = px.line(daily_sales, 
                               x='order_date', 
                               y='gmv',
                               title='Daily GMV Trend',
                               labels={'order_date': 'Date', 'gmv': 'GMV (₹)'})
        fig_daily_gmv.update_traces(line_color='#636EFA')
        fig_daily_gmv.update_layout(
            showlegend=False,
            xaxis_title="Date",
            yaxis_title="GMV (₹)",
            hovermode='x unified'
        )
        results['daily_gmv'] = fig_daily_gmv

        # 2. Daily Units Sold Trend
        fig_daily_units = px.line(daily_sales, 
                                 x='order_date', 
                                 y='units',
                                 title='Daily Units Sold Trend',
                                 labels={'order_date': 'Date', 'units': 'Units Sold'})
        fig_daily_units.update_traces(line_color='#EF553B')
        fig_daily_units.update_layout(
            showlegend=False,
            xaxis_title="Date",
            yaxis_title="Units Sold",
            hovermode='x unified'
        )
        results['daily_units'] = fig_daily_units

        # 3. Combined Monthly GMV and Units Trend
        fig_monthly = make_subplots(specs=[[{"secondary_y": True}]])
        fig_monthly.add_trace(
            go.Scatter(x=monthly_sales['order_date'], 
                      y=monthly_sales['gmv'], 
                      name="GMV",
                      line=dict(color='#636EFA')),
            secondary_y=False,
        )
        fig_monthly.add_trace(
            go.Scatter(x=monthly_sales['order_date'], 
                      y=monthly_sales['units'], 
                      name="Units Sold",
                      line=dict(color='#EF553B')),
            secondary_y=True,
        )
        fig_monthly.update_layout(
            title='Monthly GMV and Units Sold Trend',
            xaxis_title="Month",
            hovermode='x unified'
        )
        fig_monthly.update_yaxes(title_text="GMV (₹)", secondary_y=False)
        fig_monthly.update_yaxes(title_text="Units Sold", secondary_y=True)
        results['monthly_combined'] = fig_monthly

        # 4. Weekly Trend
        fig_weekly = make_subplots(specs=[[{"secondary_y": True}]])
        fig_weekly.add_trace(
            go.Scatter(x=weekly_sales['week'], 
                      y=weekly_sales['gmv'], 
                      name="GMV",
                      line=dict(color='#636EFA')),
            secondary_y=False,
        )
        fig_weekly.add_trace(
            go.Scatter(x=weekly_sales['week'], 
                      y=weekly_sales['units'], 
                      name="Units Sold",
                      line=dict(color='#EF553B')),
            secondary_y=True,
        )
        fig_weekly.update_layout(
            title='Weekly GMV and Units Sold Trend',
            xaxis_title="Week Number",
            hovermode='x unified'
        )
        fig_weekly.update_yaxes(title_text="GMV (₹)", secondary_y=False)
        fig_weekly.update_yaxes(title_text="Units Sold", secondary_y=True)
        results['weekly_combined'] = fig_weekly

        # 5. Calculate and display trend statistics
        trend_stats = pd.DataFrame([
            ['Total GMV', daily_sales['gmv'].sum()],
            ['Average Daily GMV', daily_sales['gmv'].mean()],
            ['Total Units Sold', daily_sales['units'].sum()],
            ['Average Daily Units', daily_sales['units'].mean()],
            ['Peak GMV Day', daily_sales.loc[daily_sales['gmv'].idxmax(), 'order_date'].strftime('%Y-%m-%d')],
            ['Peak Units Day', daily_sales.loc[daily_sales['units'].idxmax(), 'order_date'].strftime('%Y-%m-%d')],
            ['Number of Days', len(daily_sales)],
            ['GMV Growth Rate', ((daily_sales['gmv'].iloc[-1] - daily_sales['gmv'].iloc[0]) / daily_sales['gmv'].iloc[0] * 100)],
            ['Units Growth Rate', ((daily_sales['units'].iloc[-1] - daily_sales['units'].iloc[0]) / daily_sales['units'].iloc[0] * 100)]
        ], columns=['Metric', 'Value'])

        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[trend_stats['Metric'], 
                              trend_stats['Value'].apply(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Sales Trend Statistics',
            height=400
        )
        results['stats_table'] = fig_stats

        return results

    def analyze_delivery_sales_relationship(self):
        """
        Analyzes the relationship between delivery time (SLA) and sales metrics.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for delivery-sales analysis
        """
        results = {}
        
        # Filter data for SLA <= 100 days
        df_filtered = self.df[self.df['sla'] <= 100].copy()
        
        # Box Plot for GMV by SLA
        fig_box_gmv = px.box(df_filtered, 
                            x='sla',
                            y='gmv',
                            title='GMV Distribution by SLA (≤100 days)',
                            labels={'sla': 'Service Level Agreement (Days)',
                                   'gmv': 'GMV (₹)'})
        fig_box_gmv.update_layout(
            xaxis_title="SLA (Days)",
            yaxis_title="GMV (₹)",
            hovermode='x unified',
            xaxis=dict(range=[0, 100])
        )
        results['delivery_gmv_box'] = fig_box_gmv
        
        # Box Plot for Units by SLA
        fig_box_units = px.box(df_filtered,
                              x='sla',
                              y='units',
                              title='Units Distribution by SLA (≤100 days)',
                              labels={'sla': 'Service Level Agreement (Days)',
                                     'units': 'Units Sold'})
        fig_box_units.update_layout(
            xaxis_title="SLA (Days)",
            yaxis_title="Units Sold",
            hovermode='x unified',
            xaxis=dict(range=[0, 100])
        )
        results['delivery_units_box'] = fig_box_units
        
        # Scatter Plot for SLA vs GMV with Units as size
        fig_scatter = px.scatter(df_filtered,
                               x='sla',
                               y='gmv',
                               size='units',
                               title='SLA vs GMV (Size = Units Sold, SLA ≤100 days)',
                               labels={'sla': 'Service Level Agreement (Days)',
                                      'gmv': 'GMV (₹)',
                                      'units': 'Units Sold'})
        fig_scatter.update_layout(
            xaxis_title="SLA (Days)",
            yaxis_title="GMV (₹)",
            hovermode='closest',
            xaxis=dict(range=[0, 100])
        )
        results['delivery_gmv_scatter'] = fig_scatter
        
        # Calculate correlation statistics
        corr_stats = pd.DataFrame([
            ['Correlation (SLA vs GMV)', df_filtered['sla'].corr(df_filtered['gmv'])],
            ['Correlation (SLA vs Units)', df_filtered['sla'].corr(df_filtered['units'])],
            ['Average GMV for Fast Delivery (≤2 days)', df_filtered[df_filtered['sla'] <= 2]['gmv'].mean()],
            ['Average GMV for Slow Delivery (>2 days)', df_filtered[df_filtered['sla'] > 2]['gmv'].mean()],
            ['Average Units for Fast Delivery (≤2 days)', df_filtered[df_filtered['sla'] <= 2]['units'].mean()],
            ['Average Units for Slow Delivery (>2 days)', df_filtered[df_filtered['sla'] > 2]['units'].mean()],
            ['Orders with SLA > 100 days', len(self.df[self.df['sla'] > 100])]  # Additional statistic
        ], columns=['Metric', 'Value'])
        
        fig_corr_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                       fill_color='paleturquoise',
                       align='left'),
            cells=dict(values=[corr_stats['Metric'],
                             corr_stats['Value'].apply(lambda x: f'{x:,.2f}')],
                      fill_color='lavender',
                      align='left'))
        ])
        fig_corr_stats.update_layout(
            title='SLA-Sales Relationship Statistics (SLA ≤100 days)',
            height=400
        )
        results['delivery_sales_stats'] = fig_corr_stats
        
        return results

    def analyze_payment_type_gmv(self):
        """
        Analyzes the relationship between payment types and GMV.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for payment type vs GMV analysis
        """
        results = {}
        
        # Group data by payment type and calculate metrics
        payment_gmv = self.df.groupby('order_payment_type').agg({
            'gmv': ['sum', 'mean', 'count'],
            'units': ['sum', 'mean']
        }).reset_index()
        
        # Flatten the multi-index columns
        payment_gmv.columns = ['_'.join(col).strip('_') for col in payment_gmv.columns.values]
        
        # Rename columns for clarity
        payment_gmv = payment_gmv.rename(columns={
            'order_payment_type': 'Payment Type',
            'gmv_sum': 'Total GMV',
            'gmv_mean': 'Average GMV',
            'gmv_count': 'Order Count',
            'units_sum': 'Total Units',
            'units_mean': 'Average Units'
        })
        
        # Sort by Total GMV for better visualization
        payment_gmv = payment_gmv.sort_values('Total GMV', ascending=False)
        
        # Create bar chart for Total GMV by Payment Type
        fig_total_gmv = px.bar(
            payment_gmv,
            x='Payment Type',
            y='Total GMV',
            title='Total GMV by Payment Type',
            labels={'Payment Type': 'Payment Method', 'Total GMV': 'Total GMV (₹)'},
            color='Total GMV',
            color_continuous_scale='Viridis'
        )
        fig_total_gmv.update_layout(
            xaxis_title="Payment Method",
            yaxis_title="Total GMV (₹)",
            xaxis={'categoryorder': 'total descending'}
        )
        results['payment_total_gmv'] = fig_total_gmv
        
        # Create bar chart for Average GMV by Payment Type
        fig_avg_gmv = px.bar(
            payment_gmv,
            x='Payment Type',
            y='Average GMV',
            title='Average GMV by Payment Type',
            labels={'Payment Type': 'Payment Method', 'Average GMV': 'Average GMV (₹)'},
            color='Average GMV',
            color_continuous_scale='Viridis'
        )
        fig_avg_gmv.update_layout(
            xaxis_title="Payment Method",
            yaxis_title="Average GMV (₹)",
            xaxis={'categoryorder': 'total descending'}
        )
        results['payment_avg_gmv'] = fig_avg_gmv
        
        # Create combined visualization (scatter plot)
        fig_combined = px.scatter(
            payment_gmv,
            x='Average GMV',
            y='Order Count',
            size='Total GMV',
            color='Payment Type',
            hover_name='Payment Type',
            title='Payment Methods: Average GMV vs Order Count',
            labels={
                'Average GMV': 'Average GMV per Order (₹)',
                'Order Count': 'Number of Orders',
                'Total GMV': 'Total GMV (₹)'
            }
        )
        fig_combined.update_layout(
            xaxis_title="Average GMV per Order (₹)",
            yaxis_title="Number of Orders",
            hovermode='closest'
        )
        results['payment_combined'] = fig_combined
        
        # Create statistics table
        payment_stats = pd.DataFrame([
            ['Highest GMV Payment Method', payment_gmv.iloc[0]['Payment Type']],
            ['Highest Average GMV Payment Method', payment_gmv.loc[payment_gmv['Average GMV'].idxmax(), 'Payment Type']],
            ['Most Popular Payment Method', payment_gmv.loc[payment_gmv['Order Count'].idxmax(), 'Payment Type']],
            ['Number of Payment Methods', len(payment_gmv)],
            ['GMV Ratio (Top/Bottom Method)', payment_gmv.iloc[0]['Total GMV'] / payment_gmv.iloc[-1]['Total GMV']],
            ['Average GMV Ratio (Top/Bottom Method)', payment_gmv['Average GMV'].max() / payment_gmv['Average GMV'].min()]
        ], columns=['Metric', 'Value'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[payment_stats['Metric'], 
                              payment_stats['Value'].apply(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Payment Type vs GMV Statistics',
            height=400
        )
        results['payment_stats'] = fig_stats
        
        return results

    def analyze_pincode_gmv(self):
        """
        Analyzes the relationship between geographic regions (pincodes) and GMV.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for pincode vs GMV analysis
        """
        results = {}
        
        # Group data by pincode and calculate metrics
        pincode_gmv = self.df.groupby('pincode').agg({
            'gmv': ['sum', 'mean', 'count'],
            'units': ['sum', 'mean'],
            'cust_id': pd.Series.nunique  # Count unique customers
        }).reset_index()
        
        # Flatten the multi-index columns
        pincode_gmv.columns = ['_'.join(col).strip('_') for col in pincode_gmv.columns.values]
        
        # Rename columns for clarity
        pincode_gmv = pincode_gmv.rename(columns={
            'pincode': 'Pincode',
            'gmv_sum': 'Total GMV',
            'gmv_mean': 'Average GMV',
            'gmv_count': 'Order Count',
            'units_sum': 'Total Units',
            'units_mean': 'Average Units',
            'cust_id_nunique': 'Unique Customers'
        })
        
        # Sort by Total GMV for better visualization
        pincode_gmv = pincode_gmv.sort_values('Total GMV', ascending=False)
        
        # Create a top 20 pincodes dataframe for visualization
        top_pincodes = pincode_gmv.head(20).copy()
        
        # Create bar chart for Top 20 Pincodes by Total GMV
        fig_top_gmv = px.bar(
            top_pincodes,
            x='Pincode',
            y='Total GMV',
            title='Top 20 Pincodes by Total GMV',
            labels={'Pincode': 'Pincode', 'Total GMV': 'Total GMV (₹)'},
            color='Total GMV',
            color_continuous_scale='Viridis'
        )
        fig_top_gmv.update_layout(
            xaxis_title="Pincode",
            yaxis_title="Total GMV (₹)",
            xaxis={'categoryorder': 'total descending'}
        )
        results['pincode_top_gmv'] = fig_top_gmv
        
        # Create bar chart for Top 20 Pincodes by Average GMV
        top_avg_pincodes = pincode_gmv.sort_values('Average GMV', ascending=False).head(20)
        fig_avg_gmv = px.bar(
            top_avg_pincodes,
            x='Pincode',
            y='Average GMV',
            title='Top 20 Pincodes by Average GMV',
            labels={'Pincode': 'Pincode', 'Average GMV': 'Average GMV (₹)'},
            color='Average GMV',
            color_continuous_scale='Viridis'
        )
        fig_avg_gmv.update_layout(
            xaxis_title="Pincode",
            yaxis_title="Average GMV (₹)",
            xaxis={'categoryorder': 'total descending'}
        )
        results['pincode_avg_gmv'] = fig_avg_gmv
        
        # Create scatter plot for Order Count vs Average GMV with bubble size as Total GMV
        fig_scatter = px.scatter(
            top_pincodes,
            x='Average GMV',
            y='Order Count',
            size='Total GMV',
            color='Unique Customers',
            hover_name='Pincode',
            title='Top 20 Pincodes: Average GMV vs Order Count',
            labels={
                'Average GMV': 'Average GMV per Order (₹)',
                'Order Count': 'Number of Orders',
                'Total GMV': 'Total GMV (₹)',
                'Unique Customers': 'Number of Unique Customers'
            }
        )
        fig_scatter.update_layout(
            xaxis_title="Average GMV per Order (₹)",
            yaxis_title="Number of Orders",
            hovermode='closest'
        )
        results['pincode_scatter'] = fig_scatter
        
        # Create pincode clusters based on first 2 digits (region)
        self.df['pincode_region'] = self.df['pincode'].astype(str).str[:2]
        
        # Group by pincode region
        region_gmv = self.df.groupby('pincode_region').agg({
            'gmv': ['sum', 'mean', 'count'],
            'units': ['sum', 'mean'],
            'cust_id': pd.Series.nunique,  # Count unique customers
            'pincode': pd.Series.nunique  # Count unique pincodes in region
        }).reset_index()
        
        # Flatten the multi-index columns
        region_gmv.columns = ['_'.join(col).strip('_') for col in region_gmv.columns.values]
        
        # Rename columns for clarity
        region_gmv = region_gmv.rename(columns={
            'pincode_region': 'Region',
            'gmv_sum': 'Total GMV',
            'gmv_mean': 'Average GMV',
            'gmv_count': 'Order Count',
            'units_sum': 'Total Units',
            'units_mean': 'Average Units',
            'cust_id_nunique': 'Unique Customers',
            'pincode_nunique': 'Unique Pincodes'
        })
        
        # Sort by Total GMV for better visualization
        region_gmv = region_gmv.sort_values('Total GMV', ascending=False)
        
        # Create bar chart for Regions by Total GMV
        fig_region_gmv = px.bar(
            region_gmv,
            x='Region',
            y='Total GMV',
            title='Regions by Total GMV',
            labels={'Region': 'Region Code', 'Total GMV': 'Total GMV (₹)'},
            color='Total GMV',
            color_continuous_scale='Viridis'
        )
        fig_region_gmv.update_layout(
            xaxis_title="Region Code",
            yaxis_title="Total GMV (₹)",
            xaxis={'categoryorder': 'total descending'}
        )
        results['region_total_gmv'] = fig_region_gmv
        
        # Create bubble chart for regions
        fig_region_bubble = px.scatter(
            region_gmv,
            x='Average GMV',
            y='Unique Customers',
            size='Total GMV',
            color='Region',
            hover_name='Region',
            title='Regions: Average GMV vs Unique Customers',
            labels={
                'Average GMV': 'Average GMV per Order (₹)',
                'Unique Customers': 'Number of Unique Customers',
                'Total GMV': 'Total GMV (₹)',
                'Region': 'Region Code'
            },
            text='Region'
        )
        fig_region_bubble.update_layout(
            xaxis_title="Average GMV per Order (₹)",
            yaxis_title="Number of Unique Customers",
            hovermode='closest'
        )
        results['region_bubble'] = fig_region_bubble
        
        # Create statistics table
        pincode_stats = pd.DataFrame([
            ['Total Number of Pincodes', len(pincode_gmv)],
            ['Top Pincode by GMV', top_pincodes.iloc[0]['Pincode']],
            ['Top Pincode Total GMV', top_pincodes.iloc[0]['Total GMV']],
            ['Top Pincode by Average GMV', top_avg_pincodes.iloc[0]['Pincode']],
            ['Top Pincode Average GMV', top_avg_pincodes.iloc[0]['Average GMV']],
            ['Most Orders Pincode', pincode_gmv.loc[pincode_gmv['Order Count'].idxmax(), 'Pincode']],
            ['Most Orders Count', pincode_gmv['Order Count'].max()],
            ['Top Region by GMV', region_gmv.iloc[0]['Region']],
            ['Top Region Total GMV', region_gmv.iloc[0]['Total GMV']],
            ['GMV Concentration (Top 20 / Total)', top_pincodes['Total GMV'].sum() / pincode_gmv['Total GMV'].sum()]
        ], columns=['Metric', 'Value'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[pincode_stats['Metric'], 
                              pincode_stats['Value'].apply(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Pincode/Geographic Analysis Statistics',
            height=400
        )
        results['pincode_stats'] = fig_stats
        
        return results

    def analyze_price_sensitivity(self):
        """
        Analyzes the relationship between product price points (MRP) and units sold.
        Creates price brackets and analyzes sales performance in each bracket.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for price sensitivity analysis
        """
        results = {}
        
        # Ensure product_mrp is numeric
        self.df['product_mrp'] = pd.to_numeric(self.df['product_mrp'], errors='coerce')
        
        # Filter out rows with missing MRP
        df_filtered = self.df.dropna(subset=['product_mrp']).copy()
        
        # Create price brackets
        price_ranges = [0, 500, 1000, 2000, 5000, 10000, float('inf')]
        price_labels = ['0-500', '501-1000', '1001-2000', '2001-5000', '5001-10000', '10000+']
        
        df_filtered['price_bracket'] = pd.cut(df_filtered['product_mrp'], 
                                             bins=price_ranges, 
                                             labels=price_labels, 
                                             right=False)
        
        # Group by price bracket and calculate metrics
        price_analysis = df_filtered.groupby('price_bracket').agg({
            'gmv': ['sum', 'mean'],
            'units': ['sum', 'mean', 'count'],
            'order_id': pd.Series.nunique,  # Count unique orders
            'cust_id': pd.Series.nunique    # Count unique customers
        }).reset_index()
        
        # Flatten the multi-index columns
        price_analysis.columns = ['_'.join(col).strip('_') for col in price_analysis.columns.values]
        
        # Rename columns for clarity
        price_analysis = price_analysis.rename(columns={
            'price_bracket': 'Price Bracket',
            'gmv_sum': 'Total GMV',
            'gmv_mean': 'Average GMV',
            'units_sum': 'Total Units',
            'units_mean': 'Average Units',
            'units_count': 'Number of Transactions',
            'order_id_nunique': 'Unique Orders',
            'cust_id_nunique': 'Unique Customers'
        })
        
        # Calculate additional metrics
        price_analysis['Average Order Value'] = price_analysis['Total GMV'] / price_analysis['Unique Orders']
        price_analysis['Units per Customer'] = price_analysis['Total Units'] / price_analysis['Unique Customers']
        price_analysis['GMV per Customer'] = price_analysis['Total GMV'] / price_analysis['Unique Customers']
        
        # Create bar chart for Total Units by Price Bracket
        fig_units = px.bar(
            price_analysis,
            x='Price Bracket',
            y='Total Units',
            title='Total Units Sold by Price Bracket',
            labels={'Price Bracket': 'Price Range (₹)', 'Total Units': 'Total Units Sold'},
            color='Total Units',
            color_continuous_scale='Viridis'
        )
        fig_units.update_layout(
            xaxis_title="Price Range (₹)",
            yaxis_title="Total Units Sold",
            xaxis={'categoryorder': 'array', 'categoryarray': price_labels}
        )
        results['price_units'] = fig_units
        
        # Create bar chart for Total GMV by Price Bracket
        fig_gmv = px.bar(
            price_analysis,
            x='Price Bracket',
            y='Total GMV',
            title='Total GMV by Price Bracket',
            labels={'Price Bracket': 'Price Range (₹)', 'Total GMV': 'Total GMV (₹)'},
            color='Total GMV',
            color_continuous_scale='Viridis'
        )
        fig_gmv.update_layout(
            xaxis_title="Price Range (₹)",
            yaxis_title="Total GMV (₹)",
            xaxis={'categoryorder': 'array', 'categoryarray': price_labels}
        )
        results['price_gmv'] = fig_gmv
        
        # Create line chart for Average Units per Transaction by Price Bracket
        fig_avg_units = px.line(
            price_analysis,
            x='Price Bracket',
            y='Average Units',
            title='Average Units per Transaction by Price Bracket',
            labels={'Price Bracket': 'Price Range (₹)', 'Average Units': 'Average Units per Transaction'},
            markers=True
        )
        fig_avg_units.update_layout(
            xaxis_title="Price Range (₹)",
            yaxis_title="Average Units per Transaction",
            xaxis={'categoryorder': 'array', 'categoryarray': price_labels}
        )
        results['price_avg_units'] = fig_avg_units
        
        # Create combined visualization (bar and line)
        fig_combined = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add bar chart for Total Units
        fig_combined.add_trace(
            go.Bar(
                x=price_analysis['Price Bracket'],
                y=price_analysis['Total Units'],
                name='Total Units Sold',
                marker_color='royalblue'
            ),
            secondary_y=False
        )
        
        # Add line chart for Average Order Value
        fig_combined.add_trace(
            go.Scatter(
                x=price_analysis['Price Bracket'],
                y=price_analysis['Average Order Value'],
                name='Average Order Value',
                marker_color='firebrick',
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig_combined.update_layout(
            title='Units Sold vs Average Order Value by Price Bracket',
            xaxis_title='Price Range (₹)',
            xaxis={'categoryorder': 'array', 'categoryarray': price_labels},
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified'
        )
        
        # Update y-axes titles
        fig_combined.update_yaxes(title_text='Total Units Sold', secondary_y=False)
        fig_combined.update_yaxes(title_text='Average Order Value (₹)', secondary_y=True)
        
        results['price_combined'] = fig_combined
        
        # Create scatter plot for Units vs Customers
        fig_scatter = px.scatter(
            price_analysis,
            x='Unique Customers',
            y='Total Units',
            size='Total GMV',
            color='Price Bracket',
            hover_name='Price Bracket',
            title='Price Brackets: Customers vs Units Sold',
            labels={
                'Unique Customers': 'Number of Unique Customers',
                'Total Units': 'Total Units Sold',
                'Total GMV': 'Total GMV (₹)',
                'Price Bracket': 'Price Range (₹)'
            },
            text='Price Bracket'
        )
        fig_scatter.update_layout(
            xaxis_title="Number of Unique Customers",
            yaxis_title="Total Units Sold",
            hovermode='closest'
        )
        results['price_scatter'] = fig_scatter
        
        # Calculate price elasticity (simplified approach)
        # Sort by price bracket
        price_analysis = price_analysis.sort_values('Price Bracket')
        
        # Create statistics table
        price_stats = pd.DataFrame([
            ['Most Popular Price Bracket (Units)', price_analysis.loc[price_analysis['Total Units'].idxmax(), 'Price Bracket']],
            ['Highest GMV Price Bracket', price_analysis.loc[price_analysis['Total GMV'].idxmax(), 'Price Bracket']],
            ['Highest Average Order Value Bracket', price_analysis.loc[price_analysis['Average Order Value'].idxmax(), 'Price Bracket']],
            ['Lowest Average Order Value Bracket', price_analysis.loc[price_analysis['Average Order Value'].idxmin(), 'Price Bracket']],
            ['Price Bracket with Most Customers', price_analysis.loc[price_analysis['Unique Customers'].idxmax(), 'Price Bracket']],
            ['Units in Most Popular Bracket', price_analysis.loc[price_analysis['Total Units'].idxmax(), 'Total Units']],
            ['GMV in Highest GMV Bracket', price_analysis.loc[price_analysis['Total GMV'].idxmax(), 'Total GMV']],
            ['Units/Customer Ratio (Lowest:Highest Price)', 
             price_analysis.iloc[0]['Units per Customer'] / price_analysis.iloc[-1]['Units per Customer'] 
             if price_analysis.iloc[-1]['Units per Customer'] > 0 else 0]
        ], columns=['Metric', 'Value'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[price_stats['Metric'], 
                              price_stats['Value'].apply(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Price Sensitivity Analysis Statistics',
            height=400
        )
        results['price_stats'] = fig_stats
        
        # Additional analysis: Distribution of product prices
        fig_hist = px.histogram(
            df_filtered,
            x='product_mrp',
            nbins=50,
            title='Distribution of Product Prices (MRP)',
            labels={'product_mrp': 'Product MRP (₹)', 'count': 'Number of Transactions'},
            marginal='box'
        )
        fig_hist.update_layout(
            xaxis_title="Product MRP (₹)",
            yaxis_title="Number of Transactions"
        )
        results['price_distribution'] = fig_hist
        
        return results

    def analyze_procurement_impact(self):
        """
        Analyzes the relationship between procurement SLA and customer satisfaction metrics.
        Compares product_procurement_sla with actual delivery SLA and analyzes impact on repeat purchases.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for procurement impact analysis
        """
        results = {}
        
        # Ensure numeric types
        self.df['product_procurement_sla'] = pd.to_numeric(self.df['product_procurement_sla'], errors='coerce')
        self.df['sla'] = pd.to_numeric(self.df['sla'], errors='coerce')
        
        # Filter out rows with missing values
        df_filtered = self.df.dropna(subset=['product_procurement_sla', 'sla', 'cust_id']).copy()
        
        # Calculate SLA difference (actual delivery SLA - procurement SLA)
        df_filtered['sla_difference'] = df_filtered['sla'] - df_filtered['product_procurement_sla']
        
        # Create SLA difference categories
        df_filtered['sla_category'] = pd.cut(
            df_filtered['sla_difference'],
            bins=[-float('inf'), -5, -2, 0, 2, 5, float('inf')],
            labels=['Much Faster (>5 days)', 'Faster (2-5 days)', 'Slightly Faster (0-2 days)', 
                   'Slightly Delayed (0-2 days)', 'Delayed (2-5 days)', 'Much Delayed (>5 days)']
        )
        
        # Identify repeat customers
        # Group by customer ID and count orders
        customer_orders = df_filtered.groupby('cust_id')['order_id'].nunique().reset_index()
        customer_orders.columns = ['cust_id', 'order_count']
        
        # Merge back to get order counts for each transaction
        df_filtered = df_filtered.merge(customer_orders, on='cust_id', how='left')
        
        # Define repeat customers (more than 1 order)
        df_filtered['is_repeat_customer'] = df_filtered['order_count'] > 1
        
        # Calculate repeat purchase rate by SLA category
        sla_repeat_rate = df_filtered.groupby('sla_category').agg({
            'is_repeat_customer': 'mean',  # This gives the proportion of repeat customers
            'cust_id': 'count',  # Total number of customers in each category
            'gmv': 'mean',  # Average GMV
            'order_count': 'mean'  # Average number of orders per customer
        }).reset_index()
        
        sla_repeat_rate.columns = ['SLA Category', 'Repeat Purchase Rate', 'Customer Count', 'Average GMV', 'Average Orders']
        
        # Sort by SLA category in a logical order
        category_order = ['Much Faster (>5 days)', 'Faster (2-5 days)', 'Slightly Faster (0-2 days)', 
                         'Slightly Delayed (0-2 days)', 'Delayed (2-5 days)', 'Much Delayed (>5 days)']
        sla_repeat_rate['SLA Category'] = pd.Categorical(sla_repeat_rate['SLA Category'], categories=category_order, ordered=True)
        sla_repeat_rate = sla_repeat_rate.sort_values('SLA Category')
        
        # Create a high-quality bar chart for repeat purchase rate by SLA category
        fig_repeat_rate = px.bar(
            sla_repeat_rate,
            x='SLA Category',
            y='Repeat Purchase Rate',
            title='Impact of Delivery Time on Repeat Purchase Rate',
            labels={
                'SLA Category': 'Delivery Time vs Procurement SLA',
                'Repeat Purchase Rate': 'Repeat Purchase Rate'
            },
            color='Repeat Purchase Rate',
            color_continuous_scale='RdYlGn',  # Red to Yellow to Green scale
            text=sla_repeat_rate['Repeat Purchase Rate'].apply(lambda x: f'{x:.1%}')
        )
        
        fig_repeat_rate.update_layout(
            xaxis_title="Delivery Time vs Procurement SLA",
            yaxis_title="Repeat Purchase Rate",
            xaxis={'categoryorder': 'array', 'categoryarray': category_order},
            yaxis={'tickformat': '.0%'},
            plot_bgcolor='white',
            height=500
        )
        
        # Improve text positioning
        fig_repeat_rate.update_traces(textposition='outside')
        
        results['procurement_repeat_rate'] = fig_repeat_rate
        
        # Create a scatter plot showing the relationship between procurement SLA and actual SLA
        # with color indicating repeat purchase status
        fig_sla_scatter = px.scatter(
            df_filtered.sample(min(5000, len(df_filtered))),  # Sample to avoid overcrowding
            x='product_procurement_sla',
            y='sla',
            color='is_repeat_customer',
            title='Procurement SLA vs Actual Delivery SLA',
            labels={
                'product_procurement_sla': 'Procurement SLA (Days)',
                'sla': 'Actual Delivery SLA (Days)',
                'is_repeat_customer': 'Repeat Customer'
            },
            color_discrete_map={True: 'green', False: 'red'},
            opacity=0.7,
            marginal_x='histogram',
            marginal_y='histogram'
        )
        
        # Add reference line (y=x)
        fig_sla_scatter.add_trace(
            go.Scatter(
                x=[0, max(df_filtered['product_procurement_sla'].max(), df_filtered['sla'].max())],
                y=[0, max(df_filtered['product_procurement_sla'].max(), df_filtered['sla'].max())],
                mode='lines',
                line=dict(color='black', dash='dash'),
                name='Equal SLA Line'
            )
        )
        
        fig_sla_scatter.update_layout(
            xaxis_title="Procurement SLA (Days)",
            yaxis_title="Actual Delivery SLA (Days)",
            legend_title="Repeat Customer",
            plot_bgcolor='white',
            height=600
        )
        
        results['procurement_sla_scatter'] = fig_sla_scatter
        
        # Create a comprehensive visualization showing average orders by SLA difference
        # Group data by SLA difference (rounded to nearest integer)
        df_filtered['sla_diff_rounded'] = df_filtered['sla_difference'].round().astype(int)
        
        # Limit to a reasonable range for visualization
        sla_diff_range = df_filtered[
            (df_filtered['sla_diff_rounded'] >= -10) & 
            (df_filtered['sla_diff_rounded'] <= 10)
        ]
        
        sla_diff_analysis = sla_diff_range.groupby('sla_diff_rounded').agg({
            'cust_id': 'count',
            'order_count': 'mean',
            'gmv': 'mean',
            'is_repeat_customer': 'mean'
        }).reset_index()
        
        sla_diff_analysis.columns = ['SLA Difference', 'Transaction Count', 'Average Orders', 'Average GMV', 'Repeat Rate']
        
        # Create a dual-axis chart showing impact of SLA difference on repeat rate and average orders
        fig_impact = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add bar chart for transaction count
        fig_impact.add_trace(
            go.Bar(
                x=sla_diff_analysis['SLA Difference'],
                y=sla_diff_analysis['Transaction Count'],
                name='Transaction Count',
                marker_color='lightgray',
                opacity=0.7
            ),
            secondary_y=False
        )
        
        # Add line chart for repeat rate
        fig_impact.add_trace(
            go.Scatter(
                x=sla_diff_analysis['SLA Difference'],
                y=sla_diff_analysis['Repeat Rate'],
                name='Repeat Purchase Rate',
                marker_color='green',
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        # Add line chart for average orders
        fig_impact.add_trace(
            go.Scatter(
                x=sla_diff_analysis['SLA Difference'],
                y=sla_diff_analysis['Average Orders'],
                name='Average Orders per Customer',
                marker_color='blue',
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        # Add a reference line at x=0 (on-time delivery)
        fig_impact.add_vline(
            x=0, 
            line_width=2, 
            line_dash="dash", 
            line_color="black",
            annotation_text="On-time Delivery",
            annotation_position="top right"
        )
        
        # Update layout
        fig_impact.update_layout(
            title='Impact of SLA Difference on Customer Behavior',
            xaxis_title='SLA Difference (Actual - Procurement) in Days',
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified',
            plot_bgcolor='white',
            height=600,
            annotations=[
                dict(
                    x=-5,
                    y=1.05,
                    xref="x",
                    yref="paper",
                    text="Faster than Expected",
                    showarrow=False,
                    font=dict(color="green")
                ),
                dict(
                    x=5,
                    y=1.05,
                    xref="x",
                    yref="paper",
                    text="Slower than Expected",
                    showarrow=False,
                    font=dict(color="red")
                )
            ]
        )
        
        # Update y-axes titles
        fig_impact.update_yaxes(title_text='Transaction Count', secondary_y=False)
        fig_impact.update_yaxes(title_text='Rate / Average', secondary_y=True)
        
        results['procurement_impact'] = fig_impact
        
        # Create statistics table with key insights
        # Calculate correlation between SLA difference and repeat purchase
        corr_sla_diff_repeat = df_filtered['sla_difference'].corr(df_filtered['is_repeat_customer'].astype(int))
        
        # Calculate average metrics for on-time, early, and late deliveries
        early_delivery = df_filtered[df_filtered['sla_difference'] < 0]
        ontime_delivery = df_filtered[df_filtered['sla_difference'] == 0]
        late_delivery = df_filtered[df_filtered['sla_difference'] > 0]
        
        proc_stats = pd.DataFrame([
            ['Correlation: SLA Difference vs Repeat Purchase', corr_sla_diff_repeat],
            ['Repeat Rate: Early Delivery', early_delivery['is_repeat_customer'].mean()],
            ['Repeat Rate: On-time Delivery', ontime_delivery['is_repeat_customer'].mean() if len(ontime_delivery) > 0 else 0],
            ['Repeat Rate: Late Delivery', late_delivery['is_repeat_customer'].mean()],
            ['Average Orders: Early Delivery', early_delivery['order_count'].mean()],
            ['Average Orders: On-time Delivery', ontime_delivery['order_count'].mean() if len(ontime_delivery) > 0 else 0],
            ['Average Orders: Late Delivery', late_delivery['order_count'].mean()],
            ['Average GMV: Early Delivery', early_delivery['gmv'].mean()],
            ['Average GMV: On-time Delivery', ontime_delivery['gmv'].mean() if len(ontime_delivery) > 0 else 0],
            ['Average GMV: Late Delivery', late_delivery['gmv'].mean()],
            ['Percentage of Early Deliveries', len(early_delivery) / len(df_filtered)],
            ['Percentage of Late Deliveries', len(late_delivery) / len(df_filtered)]
        ], columns=['Metric', 'Value'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[proc_stats['Metric'], 
                              proc_stats['Value'].apply(lambda x: f'{x:.2f}%' if isinstance(x, float) and 'Correlation' not in proc_stats['Metric'][proc_stats['Value'] == x].values[0] else f'{x:,.2f}')],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Procurement SLA Impact Statistics',
            height=500
        )
        results['procurement_stats'] = fig_stats
        
        return results

    def analyze_customer_frequency(self):
        """
        Analyzes the relationship between customer purchase frequency and GMV.
        Groups by customer ID, calculates purchase frequency, and analyzes correlation with GMV.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for customer frequency analysis
        """
        results = {}
        
        # Group by customer ID and calculate metrics
        customer_metrics = self.df.groupby('cust_id').agg({
            'order_id': 'nunique',  # Count unique orders (purchase frequency)
            'gmv': 'sum',           # Total GMV
            'units': 'sum',         # Total units
            'order_date': ['min', 'max']  # First and last order dates - using strings instead of functions
        }).reset_index()
        
        # Flatten the multi-index columns
        customer_metrics.columns = ['_'.join(col).strip('_') for col in customer_metrics.columns.values]
        
        # Rename columns for clarity
        customer_metrics = customer_metrics.rename(columns={
            'cust_id': 'Customer ID',
            'order_id_nunique': 'Purchase Frequency',
            'gmv_sum': 'Total GMV',
            'units_sum': 'Total Units',
            'order_date_min': 'First Purchase',
            'order_date_max': 'Last Purchase'
        })
        
        # Calculate additional metrics
        customer_metrics['Average GMV per Order'] = customer_metrics['Total GMV'] / customer_metrics['Purchase Frequency']
        customer_metrics['Average Units per Order'] = customer_metrics['Total Units'] / customer_metrics['Purchase Frequency']
        
        # Calculate customer lifetime (days between first and last purchase)
        customer_metrics['Customer Lifetime (Days)'] = (
            customer_metrics['Last Purchase'] - customer_metrics['First Purchase']
        ).dt.days
        
        # For customers with only one purchase, set lifetime to 0
        customer_metrics['Customer Lifetime (Days)'] = customer_metrics['Customer Lifetime (Days)'].fillna(0)
        
        # Create customer segments based on purchase frequency
        # Fix: Ensure we have one fewer label than bin edges
        frequency_bins = [1, 2, 3, 5, 10, float('inf')]  # 6 bin edges
        frequency_labels = ['1', '2-3', '4-5', '6-10', '11+']  # 5 labels
        
        customer_metrics['Frequency Segment'] = pd.cut(
            customer_metrics['Purchase Frequency'], 
            bins=frequency_bins,
            labels=frequency_labels,
            right=False
        )
        
        # Create a high-quality scatter plot showing relationship between purchase frequency and total GMV
        # Use log scale for better visualization of distribution
        fig_scatter = px.scatter(
            customer_metrics,
            x='Purchase Frequency',
            y='Total GMV',
            color='Frequency Segment',
            size='Total Units',
            hover_data=['Average GMV per Order', 'Customer Lifetime (Days)'],
            title='Customer Purchase Frequency vs Total GMV',
            labels={
                'Purchase Frequency': 'Number of Purchases',
                'Total GMV': 'Total GMV (₹)',
                'Frequency Segment': 'Purchase Frequency',
                'Total Units': 'Total Units Purchased',
                'Average GMV per Order': 'Avg GMV per Order (₹)',
                'Customer Lifetime (Days)': 'Customer Lifetime (Days)'
            },
            log_y=True,
            opacity=0.7
        )
        
        fig_scatter.update_layout(
            xaxis_title="Number of Purchases",
            yaxis_title="Total GMV (₹) - Log Scale",
            legend_title="Purchase Frequency",
            plot_bgcolor='white',
            height=600
        )
        
        results['frequency_gmv_scatter'] = fig_scatter
        
        # Create a box plot showing GMV distribution by frequency segment
        fig_box = px.box(
            customer_metrics,
            x='Frequency Segment',
            y='Average GMV per Order',
            color='Frequency Segment',
            title='Average GMV per Order by Purchase Frequency',
            labels={
                'Frequency Segment': 'Purchase Frequency',
                'Average GMV per Order': 'Average GMV per Order (₹)'
            },
            notched=True
        )
        
        fig_box.update_layout(
            xaxis_title="Purchase Frequency",
            yaxis_title="Average GMV per Order (₹)",
            showlegend=False,
            plot_bgcolor='white',
            height=500
        )
        
        results['frequency_gmv_box'] = fig_box
        
        # Aggregate metrics by frequency segment
        segment_metrics = customer_metrics.groupby('Frequency Segment').agg({
            'Customer ID': 'count',
            'Total GMV': 'sum',
            'Total Units': 'sum',
            'Average GMV per Order': 'mean',
            'Customer Lifetime (Days)': 'mean'
        }).reset_index()
        
        # Calculate percentage of total GMV and customers
        total_gmv = segment_metrics['Total GMV'].sum()
        total_customers = segment_metrics['Customer ID'].sum()
        
        segment_metrics['% of Total GMV'] = segment_metrics['Total GMV'] / total_gmv * 100
        segment_metrics['% of Customers'] = segment_metrics['Customer ID'] / total_customers * 100
        segment_metrics['GMV per Customer'] = segment_metrics['Total GMV'] / segment_metrics['Customer ID']
        
        # Create a comprehensive dual-axis chart showing customer distribution and GMV contribution
        fig_segments = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add bar chart for customer count
        fig_segments.add_trace(
            go.Bar(
                x=segment_metrics['Frequency Segment'],
                y=segment_metrics['Customer ID'],
                name='Number of Customers',
                marker_color='royalblue',
                opacity=0.7,
                text=segment_metrics['Customer ID'],
                textposition='auto'
            ),
            secondary_y=False
        )
        
        # Add line chart for % of total GMV
        fig_segments.add_trace(
            go.Scatter(
                x=segment_metrics['Frequency Segment'],
                y=segment_metrics['% of Total GMV'],
                name='% of Total GMV',
                marker_color='firebrick',
                mode='lines+markers+text',
                text=segment_metrics['% of Total GMV'].apply(lambda x: f'{x:.1f}%'),
                textposition='top center'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig_segments.update_layout(
            title='Customer Distribution and GMV Contribution by Purchase Frequency',
            xaxis_title='Purchase Frequency',
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified',
            plot_bgcolor='white',
            height=500,
            barmode='group'
        )
        
        # Update y-axes titles
        fig_segments.update_yaxes(title_text='Number of Customers', secondary_y=False)
        fig_segments.update_yaxes(title_text='% of Total GMV', secondary_y=True, ticksuffix='%')
        
        results['frequency_segments'] = fig_segments
        
        # Create a heatmap showing the relationship between purchase frequency and average GMV
        # First, create frequency and GMV bins
        try:
            customer_metrics['GMV Bin'] = pd.qcut(
                customer_metrics['Average GMV per Order'],
                q=5,
                labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
            )
            
            # Create a cross-tabulation
            heatmap_data = pd.crosstab(
                customer_metrics['Frequency Segment'],
                customer_metrics['GMV Bin'],
                values=customer_metrics['Total GMV'],
                aggfunc='sum',
                normalize='all'
            ) * 100  # Convert to percentage
            
            # Create heatmap
            fig_heatmap = px.imshow(
                heatmap_data,
                text_auto='.1f',
                labels=dict(x='Average GMV per Order', y='Purchase Frequency', color='% of Total GMV'),
                x=heatmap_data.columns,
                y=heatmap_data.index,
                color_continuous_scale='Viridis',
                title='Customer Segmentation: Purchase Frequency vs Average GMV (% of Total GMV)'
            )
            
            fig_heatmap.update_layout(
                xaxis_title='Average GMV per Order',
                yaxis_title='Purchase Frequency',
                height=500
            )
            
            results['frequency_gmv_heatmap'] = fig_heatmap
        except Exception as e:
            print(f"Warning: Could not create heatmap due to: {e}")
        
        # Calculate key statistics
        # Correlation between purchase frequency and total GMV
        corr_freq_gmv = customer_metrics['Purchase Frequency'].corr(customer_metrics['Total GMV'])
        corr_freq_avg_gmv = customer_metrics['Purchase Frequency'].corr(customer_metrics['Average GMV per Order'])
        
        # Calculate metrics for one-time vs repeat purchasers
        one_time = customer_metrics[customer_metrics['Purchase Frequency'] == 1]
        repeat = customer_metrics[customer_metrics['Purchase Frequency'] > 1]
        
        # Create statistics table
        freq_stats = pd.DataFrame([
            ['Correlation: Purchase Frequency vs Total GMV', corr_freq_gmv],
            ['Correlation: Purchase Frequency vs Avg GMV per Order', corr_freq_avg_gmv],
            ['% of Customers with Single Purchase', len(one_time) / len(customer_metrics) * 100 if len(customer_metrics) > 0 else 0],
            ['% of GMV from Single-Purchase Customers', one_time['Total GMV'].sum() / customer_metrics['Total GMV'].sum() * 100 if customer_metrics['Total GMV'].sum() > 0 else 0],
            ['Average GMV per Order (Single-Purchase)', one_time['Average GMV per Order'].mean() if len(one_time) > 0 else 0],
            ['Average GMV per Order (Repeat Customers)', repeat['Average GMV per Order'].mean() if len(repeat) > 0 else 0],
            ['GMV per Customer (Single-Purchase)', one_time['Total GMV'].sum() / len(one_time) if len(one_time) > 0 else 0],
            ['GMV per Customer (Repeat Customers)', repeat['Total GMV'].sum() / len(repeat) if len(repeat) > 0 else 0],
            ['Highest Purchase Frequency', customer_metrics['Purchase Frequency'].max() if len(customer_metrics) > 0 else 0],
            ['% of GMV from Top 10% Customers', 
             customer_metrics.nlargest(max(1, int(len(customer_metrics) * 0.1)), 'Total GMV')['Total GMV'].sum() / 
             customer_metrics['Total GMV'].sum() * 100 if customer_metrics['Total GMV'].sum() > 0 else 0]
        ], columns=['Metric', 'Value'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[freq_stats['Metric'], 
                              freq_stats['Value'].apply(lambda x: f'{x:.2f}%' if isinstance(x, float) and 'Correlation' not in freq_stats['Metric'][freq_stats['Value'] == x].values[0] else f'{x:,.2f}')],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Customer Purchase Frequency Analysis Statistics',
            height=500
        )
        results['frequency_stats'] = fig_stats
        
        return results

    def analyze_discount_impact(self):
        """
        Analyzes the relationship between discount percentage and units sold.
        Calculates discount as (MRP - GMV/Units)/MRP * 100, which represents 
        the percentage reduction from MRP to the actual selling price.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for discount impact analysis
        """
        results = {}
        
        # Ensure numeric types
        self.df['product_mrp'] = pd.to_numeric(self.df['product_mrp'], errors='coerce')
        self.df['gmv'] = pd.to_numeric(self.df['gmv'], errors='coerce')
        self.df['units'] = pd.to_numeric(self.df['units'], errors='coerce')
        
        # Filter out rows with missing values or zero MRP
        df_filtered = self.df.dropna(subset=['product_mrp', 'gmv', 'units']).copy()
        df_filtered = df_filtered[df_filtered['product_mrp'] > 0]
        
        # Calculate actual selling price per unit
        df_filtered['selling_price_per_unit'] = df_filtered['gmv'] / df_filtered['units']
        
        # Calculate discount percentage: how much % off from MRP
        # Formula: ((MRP - Selling Price) / MRP) * 100
        df_filtered['discount_percentage'] = ((df_filtered['product_mrp'] - df_filtered['selling_price_per_unit']) / df_filtered['product_mrp']) * 100
        
        # Filter out unreasonable discount percentages (e.g., negative or extremely high)
        df_filtered = df_filtered[(df_filtered['discount_percentage'] >= 0) & (df_filtered['discount_percentage'] <= 100)]
        
        # Create discount brackets
        discount_bins = [0, 10, 20, 30, 40, 50, 100]
        discount_labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-100%']
        
        df_filtered['discount_bracket'] = pd.cut(
            df_filtered['discount_percentage'],
            bins=discount_bins,
            labels=discount_labels,
            right=False
        )
        
        # Group by discount bracket and calculate metrics
        discount_analysis = df_filtered.groupby('discount_bracket').agg({
            'gmv': ['sum', 'mean'],
            'units': ['sum', 'mean', 'count'],
            'order_id': pd.Series.nunique,
            'cust_id': pd.Series.nunique
        }).reset_index()
        
        # Flatten the multi-index columns
        discount_analysis.columns = ['_'.join(col).strip('_') for col in discount_analysis.columns.values]
        
        # Rename columns for clarity
        discount_analysis = discount_analysis.rename(columns={
            'discount_bracket': 'Discount Bracket',
            'gmv_sum': 'Total GMV',
            'gmv_mean': 'Average GMV',
            'units_sum': 'Total Units',
            'units_mean': 'Average Units per Order',
            'units_count': 'Number of Transactions',
            'order_id_nunique': 'Unique Orders',
            'cust_id_nunique': 'Unique Customers'
        })
        
        # Calculate additional metrics
        discount_analysis['GMV per Unit'] = discount_analysis['Total GMV'] / discount_analysis['Total Units']
        discount_analysis['Units per Customer'] = discount_analysis['Total Units'] / discount_analysis['Unique Customers']
        
        # Create a bar chart for Total Units by Discount Bracket
        fig_units = px.bar(
            discount_analysis,
            x='Discount Bracket',
            y='Total Units',
            title='Total Units Sold by Discount Bracket',
            labels={'Discount Bracket': 'Discount Range', 'Total Units': 'Total Units Sold'},
            color='Total Units',
            color_continuous_scale='Viridis',
            text=discount_analysis['Total Units'].apply(lambda x: f'{x:,.0f}')
        )
        fig_units.update_layout(
            xaxis_title="Discount Range",
            yaxis_title="Total Units Sold",
            xaxis={'categoryorder': 'array', 'categoryarray': discount_labels},
            plot_bgcolor='white'
        )
        fig_units.update_traces(textposition='outside')
        results['discount_units'] = fig_units
        
        # Create a bar chart for Total GMV by Discount Bracket
        fig_gmv = px.bar(
            discount_analysis,
            x='Discount Bracket',
            y='Total GMV',
            title='Total GMV by Discount Bracket',
            labels={'Discount Bracket': 'Discount Range', 'Total GMV': 'Total GMV (₹)'},
            color='Total GMV',
            color_continuous_scale='Viridis',
            text=discount_analysis['Total GMV'].apply(lambda x: f'{x:,.0f}')
        )
        fig_gmv.update_layout(
            xaxis_title="Discount Range",
            yaxis_title="Total GMV (₹)",
            xaxis={'categoryorder': 'array', 'categoryarray': discount_labels},
            plot_bgcolor='white'
        )
        fig_gmv.update_traces(textposition='outside')
        results['discount_gmv'] = fig_gmv
        
        # Create a dual-axis chart showing Units and GMV per Unit by Discount Bracket
        fig_combined = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add bar chart for Total Units
        fig_combined.add_trace(
            go.Bar(
                x=discount_analysis['Discount Bracket'],
                y=discount_analysis['Total Units'],
                name='Total Units Sold',
                marker_color='royalblue',
                opacity=0.7
            ),
            secondary_y=False
        )
        
        # Add line chart for GMV per Unit
        fig_combined.add_trace(
            go.Scatter(
                x=discount_analysis['Discount Bracket'],
                y=discount_analysis['GMV per Unit'],
                name='GMV per Unit',
                marker_color='firebrick',
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig_combined.update_layout(
            title='Impact of Discount on Units Sold and GMV per Unit',
            xaxis_title='Discount Range',
            xaxis={'categoryorder': 'array', 'categoryarray': discount_labels},
            legend=dict(x=0.01, y=0.99),
            hovermode='x unified',
            plot_bgcolor='white'
        )
        
        # Update y-axes titles
        fig_combined.update_yaxes(title_text='Total Units Sold', secondary_y=False)
        fig_combined.update_yaxes(title_text='GMV per Unit (₹)', secondary_y=True)
        
        results['discount_combined'] = fig_combined
        
        # Create a scatter plot showing relationship between discount percentage and units sold
        # Use a sample to avoid overcrowding
        sample_size = min(5000, len(df_filtered))
        df_sample = df_filtered.sample(sample_size)
        
        fig_scatter = px.scatter(
            df_sample,
            x='discount_percentage',
            y='units',
            color='product_mrp',
            size='gmv',
            hover_data=['selling_price_per_unit'],
            title='Discount Percentage vs Units Sold',
            labels={
                'discount_percentage': 'Discount Percentage (%)',
                'units': 'Units Sold',
                'product_mrp': 'Product MRP (₹)',
                'gmv': 'GMV (₹)',
                'selling_price_per_unit': 'Selling Price per Unit (₹)'
            },
            color_continuous_scale='Viridis',
            opacity=0.7
        )
        fig_scatter.update_layout(
            xaxis_title="Discount Percentage (%)",
            yaxis_title="Units Sold",
            plot_bgcolor='white'
        )
        results['discount_scatter'] = fig_scatter
        
        # Calculate elasticity (simplified approach)
        # Group by rounded discount percentage for smoother curve
        df_filtered['discount_rounded'] = round(df_filtered['discount_percentage'] / 5) * 5  # Round to nearest 5%
        elasticity_data = df_filtered.groupby('discount_rounded').agg({
            'units': 'sum',
            'gmv': 'sum',
            'discount_percentage': 'mean'  # Actual average discount in this bucket
        }).reset_index()
        
        # Sort by discount percentage
        elasticity_data = elasticity_data.sort_values('discount_rounded')
        
        # Calculate elasticity (% change in units / % change in price)
        # We'll use a rolling window to calculate elasticity
        elasticity_data['prev_units'] = elasticity_data['units'].shift(1)
        elasticity_data['prev_discount'] = elasticity_data['discount_percentage'].shift(1)
        elasticity_data['price_change_pct'] = (elasticity_data['discount_percentage'] - elasticity_data['prev_discount']) / (100 - elasticity_data['prev_discount']) * 100
        elasticity_data['units_change_pct'] = (elasticity_data['units'] - elasticity_data['prev_units']) / elasticity_data['prev_units'] * 100
        
        # Calculate elasticity where we have valid data
        elasticity_data['elasticity'] = elasticity_data['units_change_pct'] / elasticity_data['price_change_pct']
        
        # Filter out extreme values and NaNs
        elasticity_data = elasticity_data.replace([np.inf, -np.inf], np.nan)
        elasticity_data = elasticity_data.dropna(subset=['elasticity'])
        elasticity_data = elasticity_data[(elasticity_data['elasticity'] > -10) & (elasticity_data['elasticity'] < 10)]
        
        # Create elasticity chart
        if len(elasticity_data) > 1:
            fig_elasticity = px.line(
                elasticity_data,
                x='discount_rounded',
                y='elasticity',
                title='Price Elasticity by Discount Percentage',
                labels={
                    'discount_rounded': 'Discount Percentage (%)',
                    'elasticity': 'Price Elasticity'
                },
                markers=True
            )
            
            # Add reference line at elasticity = -1 (unit elastic)
            fig_elasticity.add_hline(
                y=-1,
                line_dash="dash",
                line_color="red",
                annotation_text="Unit Elastic",
                annotation_position="bottom right"
            )
            
            fig_elasticity.update_layout(
                xaxis_title="Discount Percentage (%)",
                yaxis_title="Price Elasticity",
                plot_bgcolor='white'
            )
            results['discount_elasticity'] = fig_elasticity
        
        # Create statistics table
        # Find the discount bracket with the highest units sold
        max_units_bracket = discount_analysis.loc[discount_analysis['Total Units'].idxmax(), 'Discount Bracket']
        
        # Find the discount bracket with the highest GMV
        max_gmv_bracket = discount_analysis.loc[discount_analysis['Total GMV'].idxmax(), 'Discount Bracket']
        
        # Calculate average metrics by discount bracket
        discount_stats = pd.DataFrame([
            ['Most Popular Discount Bracket (Units)', max_units_bracket],
            ['Highest GMV Discount Bracket', max_gmv_bracket],
            ['Units in Most Popular Bracket', discount_analysis.loc[discount_analysis['Total Units'].idxmax(), 'Total Units']],
            ['GMV in Highest GMV Bracket', discount_analysis.loc[discount_analysis['Total GMV'].idxmax(), 'Total GMV']],
            ['Average Discount Percentage', df_filtered['discount_percentage'].mean()],
            ['Median Discount Percentage', df_filtered['discount_percentage'].median()],
            ['Correlation: Discount vs Units', df_filtered['discount_percentage'].corr(df_filtered['units'])],
            ['Correlation: Discount vs GMV', df_filtered['discount_percentage'].corr(df_filtered['gmv'])],
            ['Average Units at 0-10% Discount', 
             discount_analysis.loc[discount_analysis['Discount Bracket'] == '0-10%', 'Average Units per Order'].values[0] 
             if '0-10%' in discount_analysis['Discount Bracket'].values else 0],
            ['Average Units at 40-50% Discount', 
             discount_analysis.loc[discount_analysis['Discount Bracket'] == '40-50%', 'Average Units per Order'].values[0]
             if '40-50%' in discount_analysis['Discount Bracket'].values else 0]
        ], columns=['Metric', 'Value'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric', 'Value'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[discount_stats['Metric'], 
                              discount_stats['Value'].apply(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Discount Analysis Statistics',
            height=400
        )
        results['discount_stats'] = fig_stats
        
        return results

    def analyze_correlation_matrix(self):
        """
        Creates a correlation matrix of key numeric columns in the dataset.
        Visualizes relationships between variables like GMV, units, MRP, discount, etc.
        
        Returns:
        --------
        dict: Dictionary containing plotly figures for correlation analysis
        """
        results = {}
        
        # Ensure numeric types for key columns
        numeric_cols = ['gmv', 'units', 'product_mrp', 'sla', 'product_procurement_sla']
        df_numeric = self.df[numeric_cols].copy()
        
        # Convert all columns to numeric, coercing errors
        for col in df_numeric.columns:
            df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce')
        
        # Calculate price per unit and discount percentage
        df_numeric['selling_price_per_unit'] = df_numeric['gmv'] / df_numeric['units']
        df_numeric['discount_percentage'] = ((df_numeric['product_mrp'] - df_numeric['selling_price_per_unit']) / df_numeric['product_mrp']) * 100
        
        # Drop rows with NaN values
        df_numeric = df_numeric.dropna()
        
        # Filter out unreasonable discount percentages
        df_numeric = df_numeric[(df_numeric['discount_percentage'] >= 0) & (df_numeric['discount_percentage'] <= 100)]
        
        # Calculate correlation matrix
        corr_matrix = df_numeric.corr()
        
        # Create heatmap
        fig_heatmap = px.imshow(
            corr_matrix,
            text_auto='.2f',
            color_continuous_scale='RdBu_r',  # Red-Blue diverging colorscale
            title='Correlation Matrix of Key Metrics',
            labels=dict(color='Correlation Coefficient')
        )
        
        fig_heatmap.update_layout(
            height=700,
            width=700,
            plot_bgcolor='white'
        )
        
        results['correlation_heatmap'] = fig_heatmap
        
        # Create a more detailed correlation analysis for specific pairs
        key_pairs = [
            ('gmv', 'units'),
            ('product_mrp', 'units'),
            ('discount_percentage', 'units'),
            ('discount_percentage', 'gmv'),
            ('sla', 'gmv'),
            ('product_procurement_sla', 'gmv')
        ]
        
        # Create scatter plots for key pairs
        for pair in key_pairs:
            x_col, y_col = pair
            
            # Create a sample to avoid overcrowding
            sample_size = min(5000, len(df_numeric))
            df_sample = df_numeric.sample(sample_size)
            
            # Create scatter plot
            fig_scatter = px.scatter(
                df_sample,
                x=x_col,
                y=y_col,
                title=f'Correlation: {x_col.replace("_", " ").title()} vs {y_col.replace("_", " ").title()}',
                labels={
                    x_col: x_col.replace("_", " ").title(),
                    y_col: y_col.replace("_", " ").title()
                },
                opacity=0.6,
                trendline='ols',  # Add OLS trendline
                trendline_color_override='red'
            )
            
            # Calculate correlation coefficient
            corr_value = df_numeric[x_col].corr(df_numeric[y_col])
            
            # Add annotation with correlation value
            fig_scatter.add_annotation(
                x=0.95,
                y=0.05,
                xref="paper",
                yref="paper",
                text=f"Correlation: {corr_value:.3f}",
                showarrow=False,
                font=dict(size=14),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1
            )
            
            fig_scatter.update_layout(
                plot_bgcolor='white'
            )
            
            results[f'corr_{x_col}_{y_col}'] = fig_scatter
        
        # Create a statistics table with key correlations
        corr_stats = pd.DataFrame([
            ['GMV vs Units', corr_matrix.loc['gmv', 'units']],
            ['MRP vs Units', corr_matrix.loc['product_mrp', 'units']],
            ['Discount % vs Units', corr_matrix.loc['discount_percentage', 'units']],
            ['Discount % vs GMV', corr_matrix.loc['discount_percentage', 'gmv']],
            ['SLA vs GMV', corr_matrix.loc['sla', 'gmv']],
            ['Procurement SLA vs GMV', corr_matrix.loc['product_procurement_sla', 'gmv']],
            ['MRP vs Discount %', corr_matrix.loc['product_mrp', 'discount_percentage']],
            ['SLA vs Units', corr_matrix.loc['sla', 'units']]
        ], columns=['Metric Pair', 'Correlation Coefficient'])
        
        fig_stats = go.Figure(data=[go.Table(
            header=dict(values=['Metric Pair', 'Correlation Coefficient'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[corr_stats['Metric Pair'], 
                              corr_stats['Correlation Coefficient'].apply(lambda x: f'{x:.3f}')],
                       fill_color='lavender',
                       align='left'))
        ])
        fig_stats.update_layout(
            title='Key Correlation Statistics',
            height=400
        )
        results['correlation_stats'] = fig_stats
        
        return results

class AnalyticsOrchestrator:
    """
    A class that orchestrates the execution of all analytics functions.
    """
    
    def __init__(self, dataframe):
        """
        Initialize the orchestrator with a DataFrame.
        
        Parameters:
        -----------
        dataframe : pandas.DataFrame
            The input DataFrame for analysis
        """
        self.df = dataframe
        self.results = {}
    
    def run_analysis(self):
        """
        Run the sales trend analysis and store results.
        
        Returns:
        --------
        dict: Dictionary containing all analysis results
        """
        # Clean the data
        cleaner = DataCleaner(self.df)
        cleaned_data = cleaner.clean_data()
        
        # Initialize analytics and run analysis
        analytics = CustomerAnalytics(cleaned_data)
        self.results = analytics.analyze_sales_trends()
        self.results.update(analytics.analyze_delivery_sales_relationship())
        self.results.update(analytics.analyze_payment_type_gmv())
        self.results.update(analytics.analyze_pincode_gmv())
        self.results.update(analytics.analyze_price_sensitivity())
        self.results.update(analytics.analyze_procurement_impact())
        self.results.update(analytics.analyze_customer_frequency())
        self.results.update(analytics.analyze_discount_impact())
        self.results.update(analytics.analyze_correlation_matrix())
        
        return self.results
    
    def display_plots(self):
        """
        Display all plots from the analysis.
        """
        if not self.results:
            print("No results found. Please run analysis first.")
            return
        
        # Display all plots
        for plot_name, fig in self.results.items():
            if plot_name != 'insights':
                print(f"\nDisplaying {plot_name.replace('_', ' ').title()}")
                fig.show()
    
    def save_plots(self, output_dir='Graphs_Bi'):
        """
        Save all plots from the analysis to the specified directory as PNG files.
        
        Parameters:
        -----------
        output_dir : str
            Directory path where plots will be saved
        """
        import os
        
        if not self.results:
            print("No results found. Please run analysis first.")
            return
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save all plots as PNG files
        for plot_name, fig in self.results.items():
            if plot_name != 'insights':
                file_path = os.path.join(output_dir, f"{plot_name}.png")
                fig.write_image(file_path, width=1200, height=800)
                print(f"Saved {plot_name} to {file_path}")

def main():
    """
    Main function to run the analysis and display results.
    """
    # Initialize the orchestrator
    orchestrator = AnalyticsOrchestrator(df)
    
    # Run analysis
    print("Running sales trend analysis...")
    print("Analyzing delivery time and sales relationship...")
    orchestrator.run_analysis()
    
    # Display results
    print("\nDisplaying analysis results...")
    print("Note: The delivery-sales analysis includes box plots showing GMV and Units distribution")
    print("by delivery days, and a scatter plot showing the relationship between delivery time and sales.")
    orchestrator.display_plots()
    
    # Save plots to the specified directory
    print("\nSaving plots to disk...")
    orchestrator.save_plots()

if __name__ == "__main__":
    main()