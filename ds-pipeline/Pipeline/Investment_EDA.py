#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys


class DataLoader:
    """Class for loading and preprocessing investment and NPS data"""
    
    def __init__(self, filepath):
        """Initialize with the path to the Excel file"""
        self.filepath = filepath
        self.investment_data = None
        self.nps_data = None
    
    def load_investment_data(self):
        """Load and preprocess investment data from Excel"""
        print("Loading investment data...")
        data = pd.read_excel(self.filepath)
        
        # Clean up the data
        data.drop('Unnamed: 0', axis=1, inplace=True)
        data.drop([0], inplace=True)
        data.reset_index(inplace=True)
        data.drop(['index'], axis=1, inplace=True)
        
        # Set column names
        columns = data.iloc[0]
        data = data[1:]
        data.rename(columns=columns, inplace=True)
        
        self.investment_data = data
        print("Investment data loaded successfully")
        return self.investment_data
    
    def load_nps_data(self):
        """Load and preprocess NPS data from Excel"""
        print("Loading NPS data...")
        subdata = pd.read_excel(self.filepath, sheet_name='Monthly NPS Score')
        
        # Clean up and rename columns
        columns = subdata.iloc[0]
        subdata = subdata[1:]
        subdata.rename(columns=columns, inplace=True)
        
        # Standardize month-year format
        columns = {
            'July\'23': '2023-07', 'Aug\'23': '2023-08', 'Sept\'23': '2023-09',
            'Oct\'23': '2023-10', 'Nov\'23': '2023-11', 'Dec\'23': '2023-12',
            'Jan\'24': '2024-01', 'Feb\'24': '2024-02', 'Mar\'24': '2024-03',
            'Apr\'24': '2024-04', 'May\'24': '2024-05', 'June\'24': '2024-06'
        }
        subdata.rename(columns=columns, inplace=True)
        
        # Transpose the data for easier analysis
        subdata = subdata.T
        columns = subdata.iloc[0]
        subdata = subdata[1:]
        subdata.rename(columns=columns, inplace=True)
        
        self.nps_data = subdata
        print("NPS data loaded successfully")
        return self.nps_data
    
    def load_sale_calendar_data(self):
        """Load and preprocess sale calendar data"""
        print("Loading sale calendar data...")
        # This would be implemented to load sale dates if available in the Excel
        # For now, we'll use the hardcoded data from the user's query
        
        no_of_sale_days = {
            '2023-07': 2, '2023-08': 6, '2023-09': 0, '2023-10': 3, 
            '2023-11': 8, '2023-12': 7, '2024-01': 6, '2024-02': 6, 
            '2024-03': 3, '2024-04': 0, '2024-05': 3, '2024-06': 0
        }
        
        sale_date_ranges = [
            "18-19th July 2023",
            "15-17th Aug 2023",
            "28-30th Aug 2023",
            "15-17th Oct 2023",
            "7-14th Nov 2023",
            "25th Dec 2023-3rd Jan 2024",
            "20-22nd Jan 2024",
            "1-2nd Feb 2024",
            "14-15th Feb 2024",
            "20-21st Feb 2024",
            "7-9th Mar 2024",
            "25-27th May 2024"
        ]
        
        print("Sale calendar data prepared")
        return no_of_sale_days, sale_date_ranges


class InvestmentAnalyzer:
    """Class for analyzing investment data"""
    
    def __init__(self, investment_data):
        """Initialize with investment data"""
        self.data = investment_data
    
    def get_summary_statistics(self):
        """Generate summary statistics for investment data"""
        return self.data.describe()
    
    def get_total_investment_by_category(self):
        """Calculate total investment across different categories"""
        return self.data.drop(columns=["Year", "Month", "Total Investment", "Radio", "Other"]).sum()
    
    def get_correlation_matrix(self):
        """Calculate correlation matrix between investment categories"""
        return self.data.drop(columns=["Year", "Month"]).corr()
    
    def get_monthly_investment_trends(self):
        """Get monthly trends for different investment categories"""
        investment_categories = ['TV', 'Digital', 'Sponsorship', 'Content Marketing', 
                                 'Online marketing', ' Affiliates', 'SEM']
        monthly_trends = {}
        
        for category in investment_categories:
            if category in self.data.columns:
                monthly_trends[category] = self.data[category].values
                
        return monthly_trends, self.data["Year"], self.data["Month"]
    
    def get_boxplot_data(self):
        """Prepare data for boxplot visualization"""
        return self.data.melt(id_vars=["Year", "Month"], var_name="Category", value_name="Investment")


class NPSAnalyzer:
    """Class for analyzing NPS (Net Promoter Score) data"""
    
    def __init__(self, nps_data):
        """Initialize with NPS data"""
        self.data = nps_data
    
    def get_nps_trend(self):
        """Get NPS trend over time"""
        return self.data.index.tolist(), self.data["NPS"].values
    
    def get_stock_index_trend(self):
        """Get stock index trend over time"""
        return self.data.index.tolist(), self.data["Stock Index"].values
    
    def get_stock_vs_nps_data(self):
        """Get data for comparing stock index vs NPS"""
        return self.data["Stock Index"].values, self.data["NPS"].values


class SaleCalendarAnalyzer:
    """Class for analyzing sale calendar data"""
    
    def __init__(self, sale_days, sale_ranges):
        """Initialize with sale days and date ranges"""
        self.sale_days = sale_days
        self.sale_ranges = sale_ranges
        self.all_sale_dates = []
    
    def convert_to_date_ranges(self):
        """Convert the text date ranges to tuples of start and end dates"""
        from datetime import datetime
        
        date_ranges = []
        for date_range in self.sale_ranges:
            try:
                # Parse dates from strings like "18-19th July 2023"
                if '-' in date_range:
                    parts = date_range.split('-')
                    
                    # Handle special cases like "25th Dec 2023-3rd Jan 2024"
                    if any(month in parts[1] for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                        # Cross-month or cross-year range
                        start_str = parts[0].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                        end_str = parts[1].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                        
                        # Parse start date
                        start_parts = start_str.split(' ')
                        if len(start_parts) == 2:  # Day and month only
                            start_day = int(start_parts[0])
                            start_month = start_parts[1]
                            # Infer year from end date
                            end_parts = end_str.split(' ')
                            if len(end_parts) < 3:
                                print(f"Warning: Could not parse end date properly: {end_str}")
                                continue
                            start_year = end_parts[2]
                        else:  # Day, month, and year
                            start_day = int(start_parts[0])
                            start_month = start_parts[1]
                            start_year = start_parts[2]
                        
                        # Parse end date
                        end_parts = end_str.split(' ')
                        end_day = int(end_parts[0])
                        end_month = end_parts[1]
                        end_year = end_parts[2]
                        
                        # Convert to string format 'YYYY-MM-DD'
                        month_to_num = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                        }
                        
                        start_date_str = f"{start_year}-{month_to_num[start_month]}-{start_day:02d}"
                        end_date_str = f"{end_year}-{month_to_num[end_month]}-{end_day:02d}"
                        
                    else:
                        # Same month range
                        start_str = parts[0].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                        end_str = parts[1].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                        
                        # Parse start date
                        start_parts = start_str.split(' ')
                        if len(start_parts) < 3:
                            print(f"Warning: Could not parse start date properly: {start_str}")
                            continue
                            
                        start_day = int(start_parts[0])
                        start_month = start_parts[1]
                        start_year = start_parts[2]
                        
                        # Parse end date - if just a day, use start month/year
                        end_parts = end_str.split(' ')
                        if len(end_parts) == 1:  # Just a day
                            end_day = int(end_parts[0])
                            end_month = start_month
                            end_year = start_year
                        else:  # Complete date
                            end_day = int(end_parts[0])
                            end_month = end_parts[1] if len(end_parts) > 1 else start_month
                            end_year = end_parts[2] if len(end_parts) > 2 else start_year
                        
                        # Convert to string format 'YYYY-MM-DD'
                        month_to_num = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                        }
                        
                        start_date_str = f"{start_year}-{month_to_num[start_month]}-{start_day:02d}"
                        end_date_str = f"{end_year}-{month_to_num[end_month]}-{end_day:02d}"
                        
                else:
                    # Single day
                    date_str = date_range.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    parts = date_str.split(' ')
                    
                    if len(parts) < 3:
                        print(f"Warning: Could not parse date properly: {date_str}")
                        continue
                        
                    day = int(parts[0])
                    month = parts[1]
                    year = parts[2]
                    
                    # Convert to string format 'YYYY-MM-DD'
                    month_to_num = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    
                    start_date_str = end_date_str = f"{year}-{month_to_num[month]}-{day:02d}"
                
                date_ranges.append((start_date_str, end_date_str))
                
            except Exception as e:
                print(f"Error parsing date range '{date_range}': {str(e)}")
                continue
                
        return date_ranges
    
    def group_by_custom_week(self):
        """
        Group sale dates by custom week definition.
        Week 1 starts from July 3, 2023 (Monday).
        """
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Create a mapping of weeks starting from 3rd July 2023 (Monday) to 30th June 2024 (Sunday)
        start_date = datetime(2023, 7, 3)  # First Monday of July 2023
        end_date = datetime(2024, 6, 30)   # Last Sunday of June 2024
        
        # Reset weekly data based on custom week definition
        custom_weekly_data = {week: 0 for week in range(1, 53)}
        
        # Convert text date ranges to formatted sale periods
        sale_periods = []
        for date_range in self.sale_ranges:
            try:
                # Use existing parsing logic to convert to proper date format
                date_tuple = self.convert_date_range_to_tuple(date_range)
                if date_tuple:
                    sale_periods.append(date_tuple)
            except Exception as e:
                print(f"Error converting date range '{date_range}': {str(e)}")
                continue
        
        # Assign sale days to custom-defined weeks
        for start_date_str, end_date_str in sale_periods:
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
            end = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            current_date = start
            while current_date <= end:
                if current_date >= start_date and current_date <= end_date:
                    # Calculate custom week number
                    week_number = ((current_date - start_date).days // 7) + 1
                    if week_number in custom_weekly_data:
                        custom_weekly_data[week_number] += 1
                current_date += timedelta(days=1)
        
        # Create a more structured result with week labels and date ranges
        result = {}
        for week_num, count in custom_weekly_data.items():
            week_start = start_date + timedelta(days=(week_num-1)*7)
            week_end = week_start + timedelta(days=6)
            week_key = f"Week {week_num} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})"
            result[week_key] = {
                'count': count,
                'start_date': week_start,
                'end_date': week_end,
                'week_number': week_num
            }
        
        return result, custom_weekly_data, start_date, end_date
    
    def convert_date_range_to_tuple(self, date_range):
        """Convert a text date range to a tuple of start and end dates in YYYY-MM-DD format"""
        from datetime import datetime
        
        try:
            # Parse dates from strings like "18-19th July 2023"
            if '-' in date_range:
                parts = date_range.split('-')
                
                # Handle special cases like "25th Dec 2023-3rd Jan 2024"
                if any(month in parts[1] for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                    # Cross-month or cross-year range
                    start_str = parts[0].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    end_str = parts[1].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    
                    # Parse start date
                    start_parts = start_str.split(' ')
                    if len(start_parts) == 2:  # Day and month only
                        start_day = int(start_parts[0])
                        start_month = start_parts[1]
                        # Infer year from end date
                        end_parts = end_str.split(' ')
                        if len(end_parts) < 3:
                            print(f"Warning: Could not parse end date properly: {end_str}")
                            return None
                        start_year = end_parts[2]
                    else:  # Day, month, and year
                        start_day = int(start_parts[0])
                        start_month = start_parts[1]
                        start_year = start_parts[2]
                    
                    # Parse end date
                    end_parts = end_str.split(' ')
                    end_day = int(end_parts[0])
                    end_month = end_parts[1]
                    end_year = end_parts[2]
                    
                    # Convert to string format 'YYYY-MM-DD'
                    month_to_num = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    
                    start_date_str = f"{start_year}-{month_to_num[start_month]}-{start_day:02d}"
                    end_date_str = f"{end_year}-{month_to_num[end_month]}-{end_day:02d}"
                    
                else:
                    # Same month range
                    start_str = parts[0].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    end_str = parts[1].strip().replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                    
                    # Parse start date
                    start_parts = start_str.split(' ')
                    if len(start_parts) < 3:
                        print(f"Warning: Could not parse start date properly: {start_str}")
                        return None
                        
                    start_day = int(start_parts[0])
                    start_month = start_parts[1]
                    start_year = start_parts[2]
                    
                    # Parse end date - if just a day, use start month/year
                    end_parts = end_str.split(' ')
                    if len(end_parts) == 1:  # Just a day
                        end_day = int(end_parts[0])
                        end_month = start_month
                        end_year = start_year
                    else:  # Complete date
                        if len(end_parts) < 3:
                            print(f"Warning: Could not parse end date properly: {end_str}")
                            return None
                        end_day = int(end_parts[0])
                        end_month = end_parts[1]
                        end_year = end_parts[2]
                    
                    # Convert to string format 'YYYY-MM-DD'
                    month_to_num = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    
                    start_date_str = f"{start_year}-{month_to_num[start_month]}-{start_day:02d}"
                    end_date_str = f"{end_year}-{month_to_num[end_month]}-{end_day:02d}"
                    
            else:
                # Single day
                date_str = date_range.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
                parts = date_str.split(' ')
                
                if len(parts) < 3:
                    print(f"Warning: Could not parse date properly: {date_str}")
                    return None
                    
                day = int(parts[0])
                month = parts[1]
                year = parts[2]
                
                # Convert to string format 'YYYY-MM-DD'
                month_to_num = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                    'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                
                start_date_str = end_date_str = f"{year}-{month_to_num[month]}-{day:02d}"
            
            return (start_date_str, end_date_str)
            
        except Exception as e:
            print(f"Error parsing date range '{date_range}': {str(e)}")
            return None  # Return None for problematic date strings


class ComparativeAnalyzer:
    """Class for comparative analysis between different datasets"""
    
    def __init__(self, investment_data, nps_data):
        """Initialize with investment and NPS data"""
        self.investment_data = investment_data
        self.nps_data = nps_data
    
    def compare_stock_vs_investment(self):
        """Compare stock index with total investment"""
        stock_data = self.nps_data["Stock Index"].reset_index(drop=True)
        investment_data = self.investment_data["Total Investment"].reset_index(drop=True)
        months = [f"{y}-{m:02d}" for y, m in zip(self.investment_data["Year"], self.investment_data["Month"])]
        
        return months, stock_data, investment_data
    
    def compare_stock_vs_category(self, category):
        """Compare stock index with a specific investment category"""
        stock_data = self.nps_data["Stock Index"].reset_index(drop=True)
        category_data = self.investment_data[category].reset_index(drop=True)
        months = [f"{y}-{m:02d}" for y, m in zip(self.investment_data["Year"], self.investment_data["Month"])]
        
        return months, stock_data, category_data
    
    def compare_nps_vs_category(self, category):
        """Compare NPS with a specific investment category"""
        nps_data = self.nps_data["NPS"].reset_index(drop=True)
        category_data = self.investment_data[category].reset_index(drop=True)
        months = [f"{y}-{m:02d}" for y, m in zip(self.investment_data["Year"], self.investment_data["Month"])]
        
        return months, nps_data, category_data
    
    def get_all_categories(self):
        """Get list of all investment categories"""
        return ['TV', 'Digital', 'Sponsorship', 'Content Marketing', 
                'Online marketing', ' Affiliates', 'SEM']


class DataVisualizer:
    """Class for visualizing data through various plots"""
    
    def __init__(self, output_dir="Graphs_Investment"):
        """Initialize with output directory for saving plots"""
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
    
    def plot_total_investment(self, months, investment_data):
        """Plot total investment trend over time"""
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=months, 
                y=investment_data, 
                mode='lines+markers',
                name="Total Investment",
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            )
        )
        
        fig.update_layout(
            title="Total Investment Over Time",
            xaxis_title="Month-Year",
            yaxis_title="Total Investment (in Million)",
            template="plotly_white",
            width=1000,
            height=500
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "total_investment_trend.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_total_by_category(self, category_totals):
        """Plot total investment across different categories"""
        fig = px.bar(
            x=category_totals.index,
            y=category_totals.values,
            color=category_totals.values,
            color_continuous_scale='viridis',
            labels={'x': 'Category', 'y': 'Total Amount Spent (in Million)'}
        )
        
        fig.update_layout(
            title="Total Investment Across Different Categories",
            xaxis_tickangle=-45,
            template="plotly_white",
            width=1000,
            height=600
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "total_investment_by_category.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_correlation_heatmap(self, corr_matrix):
        """Plot correlation heatmap"""
        fig = px.imshow(
            corr_matrix,
            text_auto='.2f',
            color_continuous_scale='RdBu_r',
            aspect="auto",
            zmin=-1,
            zmax=1
        )
        
        fig.update_layout(
            title="Correlation Matrix of Investment Categories",
            width=800,
            height=600,
            template="plotly_white"
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "correlation_heatmap.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_monthly_trends(self, months, monthly_trends):
        """Plot monthly trends for different investment categories"""
        fig = go.Figure()
        
        for category, values in monthly_trends.items():
            if category not in ["Radio", "Other"]:  # Ignore sparse categories
                fig.add_trace(
                    go.Scatter(
                        x=months,
                        y=values,
                        mode='lines+markers',
                        name=category,
                        marker=dict(size=8)
                    )
                )
        
        fig.update_layout(
            title="Monthly Trend of Investment Categories",
            xaxis_title="Month-Year",
            yaxis_title="Investment (in Million)",
            xaxis_tickangle=-45,
            template="plotly_white",
            width=1000,
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "monthly_investment_trends.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_investment_boxplot(self, boxplot_data):
        """Plot boxplot for investment distribution"""
        # Filter out non-investment categories
        plot_data = boxplot_data[~boxplot_data['Category'].isin(['Year', 'Month', 'Total Investment'])]
        
        fig = px.box(
            plot_data,
            x="Category",
            y="Investment",
            color="Category",
            title="Investment Distribution and Outliers by Category"
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            template="plotly_white",
            showlegend=False,
            width=1200,
            height=700
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "investment_boxplot.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_nps_trend(self, months, nps_data):
        """Plot NPS trend over time"""
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=months, 
                y=nps_data, 
                mode='lines+markers',
                name="Net Promoter Score (NPS)",
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            )
        )
        
        fig.update_layout(
            title="Net Promoter Score (NPS) Over Time",
            xaxis_title="Month-Year",
            yaxis_title="Net Promoter Score (NPS)",
            template="plotly_white",
            width=1000,
            height=500
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "nps_trend.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_stock_trend(self, months, stock_data):
        """Plot stock index trend over time"""
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=months, 
                y=stock_data, 
                mode='lines+markers',
                name="Stock Index",
                line=dict(color='red', width=2),
                marker=dict(size=8)
            )
        )
        
        fig.update_layout(
            title="Stock Index Over Time",
            xaxis_title="Month-Year",
            yaxis_title="Stock Index",
            template="plotly_white",
            width=1000,
            height=500
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "stock_trend.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_stock_vs_investment_scatter(self, stock_data, investment_data):
        """Create scatter plot of stock index vs total investment"""
        fig = px.scatter(
            x=stock_data,
            y=investment_data,
            trendline="ols",
            labels={"x": "Stock Index", "y": "Total Investment"}
        )
        
        fig.update_traces(
            marker=dict(size=12, opacity=0.8),
            selector=dict(mode='markers')
        )
        
        fig.update_layout(
            title="Stock Index vs Total Investment",
            template="plotly_white",
            width=800,
            height=600
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "stock_vs_investment_scatter.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_dual_axis_trend(self, months, primary_data, primary_name, secondary_data, secondary_name):
        """Create dual-axis plot comparing two trends"""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add primary data trace
        fig.add_trace(
            go.Scatter(
                x=months, 
                y=primary_data,
                name=primary_name,
                line=dict(color='red'),
                mode='lines+markers'
            ),
            secondary_y=False
        )
        
        # Add secondary data trace
        fig.add_trace(
            go.Scatter(
                x=months, 
                y=secondary_data,
                name=secondary_name,
                line=dict(color='blue'),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
            title=f"{primary_name} and {secondary_name} Over Time",
            title_x=0.5,
            plot_bgcolor='white',
            width=1000,
            height=600,
            xaxis=dict(
                title="Month",
                showgrid=True,
                gridwidth=1,
                gridcolor='LightGray'
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        # Update y-axes titles
        fig.update_yaxes(
            title_text=primary_name, 
            secondary_y=False, 
            showgrid=True, 
            gridwidth=1, 
            gridcolor='LightGray',
            color='red'
        )
        fig.update_yaxes(
            title_text=secondary_name, 
            secondary_y=True,
            showgrid=True, 
            gridwidth=1, 
            gridcolor='LightGray',
            color='blue'
        )
        
        # Create a sanitized filename
        sanitized_primary = primary_name.replace(" ", "_").replace("/", "_")
        sanitized_secondary = secondary_name.replace(" ", "_").replace("/", "_")
        filename = f"{sanitized_primary}_vs_{sanitized_secondary}.png"
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, filename)
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        # Display the figure
        fig.show()
    
    def plot_monthly_sale_days(self, sale_days):
        """Plot monthly sale days to match the provided image"""
        # Create DataFrame for plotting
        data = pd.DataFrame(list(sale_days.items()), columns=['Month', 'Sale Days'])
        
        # Sort by month to ensure chronological order
        data['Month_dt'] = pd.to_datetime(data['Month'])
        data = data.sort_values('Month_dt')
        
        # Create the line graph
        fig = px.line(data, x='Month', y='Sale Days', markers=True,
                     title='Number of Sale Days Per Month',
                     labels={'Month': 'Month', 'Sale Days': 'Number of Sale Days'})
        
        # Update layout to match the exact styling
        fig.update_layout(
            template='plotly_white',
            xaxis=dict(
                tickangle=45,
                tickmode='array',
                tickvals=data['Month'].tolist(),
                ticktext=[m.replace('2023-', '').replace('2024-', '') for m in data['Month']],
                gridcolor='rgba(211, 211, 211, 0.5)',
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='rgba(211, 211, 211, 0.5)',
                showgrid=True,
                dtick=2,  # Tick every 2 units
                range=[0, 9]  # Y-axis range from 0 to 9
            ),
            plot_bgcolor='rgba(240, 240, 250, 0.6)',  # Light blue background
            width=1000,
            height=500,
            margin=dict(l=60, r=30, t=50, b=50)
        )
        
        # Update line and marker styling to match the image
        fig.update_traces(
            line=dict(color='royalblue', width=2),
            marker=dict(size=8, color='royalblue')
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "monthly_sale_days.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        return fig
    
    def plot_sale_weeks(self, text_data, weekly_data):
        """Plot sale days by custom week"""
        # Create DataFrame for plotting
        data = pd.DataFrame({
            'Week': list(range(1, 53)),
            'Sale Days': [weekly_data.get(week, 0) for week in range(1, 53)]
        })
        
        # Filter weeks that have sale days
        plot_data = data[data['Sale Days'] > 0]
        
        # Create the bar graph
        fig = px.bar(
            plot_data, 
            x='Week', 
            y='Sale Days',
            title='Sale Days by Custom Week (Starting from July 3, 2023)',
            labels={'Week': 'Week Number', 'Sale Days': 'Number of Sale Days'}
        )
        
        fig.update_layout(
            template='plotly_white',
            xaxis=dict(
                tickangle=0,
                tickmode='array',
                tickvals=plot_data['Week'].tolist(),
                title='Week Number',
                gridcolor='rgba(211, 211, 211, 0.5)',
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='rgba(211, 211, 211, 0.5)',
                showgrid=True,
                dtick=1,
                title='Number of Sale Days'
            ),
            plot_bgcolor='rgba(240, 240, 250, 0.6)',
            width=1000,
            height=500
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "sale_days_by_week.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        return fig
    
    def plot_weekly_heatmap(self, weekly_data, start_date):
        """Plot weekly heatmap of sale days"""
        from datetime import timedelta
        
        # Create a data grid for heatmap (12 months × ~4-5 weeks)
        num_weeks = 52
        month_labels = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 
                         'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        
        # Reshape the data into weeks of months (approximate)
        months_data = []
        week_indices = []
        
        for month_idx in range(12):
            month_start = month_idx * 4  # Approximate weeks per month
            month_end = month_start + 4
            month_weeks = [weekly_data.get(i, 0) for i in range(month_start+1, month_end+1)]
            while len(month_weeks) < 5:
                month_weeks.append(0)  # Pad to have 5 weeks per month for visualization
            months_data.append(month_weeks)
            week_indices.extend([month_idx + 1] * 5)
        
        # Convert to appropriate format for heatmap
        heatmap_data = np.array(months_data).T  # Transpose for weeks × months
        
        # Create heatmap
        weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']
        
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Month", y="Week", color="Sale Days"),
            x=month_labels,
            y=weeks,
            color_continuous_scale='Blues',
            title="Sale Days Calendar Heatmap (Jul 2023 - Jun 2024)"
        )
        
        fig.update_layout(
            width=1000, 
            height=500,
            template='plotly_white'
        )
        
        # Save the figure to file
        output_path = os.path.join(self.output_dir, "weekly_heatmap.png")
        fig.write_image(output_path)
        print(f"Saved plot to {output_path}")
        
        return fig


def run_analyzer(filepath):
    """Function to run all analyses without user choices"""
    print(f"Running analysis on file: {filepath}")
    
    # Create the output directory if it doesn't exist
    output_dir = "Graphs_Investment"
    
    # Initialize data loader and load data
    data_loader = DataLoader(filepath)
    investment_data = data_loader.load_investment_data()
    nps_data = data_loader.load_nps_data()
    sale_days, sale_ranges = data_loader.load_sale_calendar_data()
    
    # Initialize analyzers
    investment_analyzer = InvestmentAnalyzer(investment_data)
    nps_analyzer = NPSAnalyzer(nps_data)
    
    # Fix problematic date ranges and update the list
    fixed_sale_ranges = [
        "18-19th July 2023",
        "15-17th Aug 2023",
        "28-30th Aug 2023",
        "15-17th Oct 2023",
        "7-14th Nov 2023",
        "25th Dec 2023-3rd Jan 2024",
        "20-22nd Jan 2024",
        "1-2nd Feb 2024",
        "14-15th Feb 2024",
        "20-21st Feb 2024",
        "7-9th Mar 2024",
        "25-27th May 2024"
    ]
    sale_analyzer = SaleCalendarAnalyzer(sale_days, fixed_sale_ranges)
    comparative_analyzer = ComparativeAnalyzer(investment_data, nps_data)
    
    # Initialize visualizer with output directory
    visualizer = DataVisualizer(output_dir)
    
    # 1. Basic Investment Analysis
    print("\n=== Basic Investment Analysis ===")
    
    # Summary statistics
    print("\nInvestment Summary Statistics:")
    print(investment_analyzer.get_summary_statistics())
    
    # Total investment over time
    print("\nPlotting total investment over time...")
    months = [f"{y}-{m:02d}" for y, m in zip(investment_data["Year"], investment_data["Month"])]
    visualizer.plot_total_investment(months, investment_data["Total Investment"])
    
    # Total investment by category
    print("\nPlotting total investment by category...")
    category_totals = investment_analyzer.get_total_investment_by_category()
    visualizer.plot_total_by_category(category_totals)
    
    # Correlation matrix
    print("\nPlotting correlation matrix...")
    corr_matrix = investment_analyzer.get_correlation_matrix()
    visualizer.plot_correlation_heatmap(corr_matrix)
    
    # Monthly trends
    print("\nPlotting monthly investment trends...")
    monthly_trends, years, months = investment_analyzer.get_monthly_investment_trends()
    months_formatted = [f"{y}-{m:02d}" for y, m in zip(years, months)]
    visualizer.plot_monthly_trends(months_formatted, monthly_trends)
    
    # Investment distribution
    print("\nPlotting investment distribution...")
    boxplot_data = investment_analyzer.get_boxplot_data()
    visualizer.plot_investment_boxplot(boxplot_data)
    
    # 2. NPS and Stock Analysis
    print("\n=== NPS and Stock Analysis ===")
    
    # NPS trend
    print("\nPlotting NPS trend...")
    nps_months, nps_values = nps_analyzer.get_nps_trend()
    visualizer.plot_nps_trend(nps_months, nps_values)
    
    # Stock index trend
    print("\nPlotting stock index trend...")
    stock_months, stock_values = nps_analyzer.get_stock_index_trend()
    visualizer.plot_stock_trend(stock_months, stock_values)
    
    # 3. Sale Calendar Analysis
    try:
        print("\n=== Sale Calendar Analysis ===")
        
        # Plot monthly sale days graph
        print("\nPlotting monthly sale days...")
        monthly_fig = visualizer.plot_monthly_sale_days(sale_days)
        monthly_fig.show()
        
        # Group sales by week using custom definition
        print("\nGrouping sales by custom week (starting July 3, 2023)...")
        result, custom_weekly_data, custom_start_date, custom_end_date = sale_analyzer.group_by_custom_week()
        
        # Print first day of custom week definition
        print(f"\nCustom week 1 starts on: {custom_start_date.strftime('%Y-%m-%d')} (Monday)")
        print(f"Custom week schedule ends on: {custom_end_date.strftime('%Y-%m-%d')} (Sunday)")
        
        # Print sale days by custom week
        print("\nSale days by custom week:")
        for week_key, data in result.items():
            if data['count'] > 0:
                print(f"{week_key}: {data['count']} sale days")
        
        # Plot sale days by custom week
        print("\nPlotting sale days by custom week...")
        weekly_fig = visualizer.plot_sale_weeks(None, custom_weekly_data)
        weekly_fig.show()
        
        # Plot weekly heatmap
        print("\nPlotting sale days calendar heatmap...")
        heatmap_fig = visualizer.plot_weekly_heatmap(custom_weekly_data, custom_start_date)
        heatmap_fig.show()
        
    except Exception as e:
        print(f"\nSkipping Sale Calendar Analysis due to error: {str(e)}")
        print("Continuing with remaining analyses...")
    
    # 4. Comparative Analysis
    print("\n=== Comparative Analysis ===")
    
    # Stock vs Total Investment scatter
    print("\nPlotting stock index vs total investment scatter...")
    stock_vs_inv = comparative_analyzer.compare_stock_vs_investment()
    visualizer.plot_stock_vs_investment_scatter(stock_vs_inv[1], stock_vs_inv[2])
    
    # Stock vs Total Investment dual axis
    print("\nPlotting stock index vs total investment dual axis...")
    visualizer.plot_dual_axis_trend(stock_vs_inv[0], stock_vs_inv[1], "Stock Index", stock_vs_inv[2], "Total Investment")
    
    # Stock vs Categories and NPS vs Categories
    categories = comparative_analyzer.get_all_categories()
    
    print("\nPlotting stock index vs each investment category...")
    for category in categories:
        print(f"  - Plotting Stock Index vs {category}")
        months, stock_data, category_data = comparative_analyzer.compare_stock_vs_category(category)
        visualizer.plot_dual_axis_trend(months, stock_data, "Stock Index", category_data, category)
    
    print("\nPlotting NPS vs each investment category...")
    for category in categories:
        print(f"  - Plotting NPS vs {category}")
        months, nps_data, category_data = comparative_analyzer.compare_nps_vs_category(category)
        visualizer.plot_dual_axis_trend(months, nps_data, "NPS", category_data, category)
    
    print("\nAnalysis complete!")
    print(f"All plots saved to directory: {output_dir}")


if __name__ == "__main__":
    # Ask user for input file path
    print("Investment Analysis Tool")
    print("========================")
    
    # Check if file was provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = input("Please enter the path to your Excel file: ")
    
    # Run the analyzer with the provided file
    run_analyzer(input_file) 