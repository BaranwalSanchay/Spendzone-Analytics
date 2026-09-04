import os
import sys
from typing import List, Dict, Any, Optional
import glob
import logging
import time
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import BaseTool, StructuredTool
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import traceback
from sklearn.linear_model import LinearRegression

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("roi_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("roi_agent")

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)
    logger.info(f"Created plots directory at {PLOTS_DIR}")
else:
    logger.info(f"Using existing plots directory at {PLOTS_DIR}")

def get_data_manager():
    """Get or create the DataManager instance."""
    from utils.data_manager import get_data_manager
    return get_data_manager()

class ROIAgent:
    """
    Agent for calculating and analyzing marketing ROI and campaign effectiveness.
    """
    
    def __init__(self, llm: BaseChatModel, data_manager=None):
        """
        Initialize the ROI analysis agent.
        
        Args:
            llm: Language model to use for the agent
            data_manager: DataManager instance with loaded dataframes
        """
        logger.info("Initializing ROIAgent")
        self.llm = llm
        
        # Use provided data manager or get the default one
        if data_manager is None:
            self.data_manager = get_data_manager()
        else:
            self.data_manager = data_manager
            
        # Get dataframes from the data manager
        self.dataframes = self.data_manager.get_dataframes()
        
        logger.info(f"ROIAgent using {len(self.dataframes)} dataframes")
        
        # Set up tools
        self.tools = self._create_tools()
        
        # Create the agent executor - but don't initialize it yet to save API calls
        # We'll only create it when needed for custom queries
        self.agent_executor = None
        logger.info("ROIAgent initialization complete (lazy loading agent executor to save API calls)")
    
    def _load_csv_files(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from the data directory."""
        logger.info("Loading CSV files from data directory")
        dataframes = self.dataframes
        
        return dataframes
    
    def _get_data_schema(self) -> str:
        """Generate schema information about the loaded dataframes."""
        return self.data_manager.get_schema_info()

    def _create_tools(self) -> List[BaseTool]:
        """Create tools for ROI analysis."""
        logger.info("Creating tools for ROI analysis")
        
        def calculate_channel_roi(table_name: str = "Master", total_investment_column: str = "Total Investment", 
                                 channels: list = None, date_column: str = "order_date", 
                                 gmv_column: str = "gmv") -> str:
            """
            Calculate and compare ROI across marketing channels using Marketing Mix Modeling (MMM).
            
            Args:
                table_name: Name of the table containing investment and GMV data
                total_investment_column: Column name with total marketing investment data
                channels: List of marketing channel columns to analyze (if None, use default channels)
                date_column: Column name with date information
                gmv_column: Column name with GMV data
                
            Returns:
                String with ROI analysis results
            """
            logger.info(f"Tool called: calculate_channel_roi")
            result = ""
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name]
                
                # Define default channels if not provided
                if not channels:
                    channels = ["TV", "Radio", "Sponsorship", "Content Marketing", 
                               "Online marketing", " Affiliates", "SEM", "Other"]
                
                # Ensure required columns exist
                required_columns = [date_column, gmv_column, total_investment_column] + channels
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return f"Columns not found: {missing_columns}. Available columns: {', '.join(df.columns)}"
                
                # Convert date column to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                    df[date_column] = pd.to_datetime(df[date_column])
                
                # Create year-month column for aggregation
                df['year_month'] = df[date_column].dt.to_period('M')
                
                # Convert investment columns from crores to rupees
                conversion_factor = 1e7  # 1 crore = 10 million
                investment_columns = [total_investment_column] + [channel for channel in channels if channel != total_investment_column]
                df[investment_columns] = df[investment_columns] * conversion_factor
                
                # Group by month to get monthly GMV and channel investments
                monthly_data = df.groupby('year_month').agg({
                    gmv_column: 'sum',
                    total_investment_column: 'mean',
                    **{channel: 'mean' for channel in channels if channel in df.columns}
                })
                
                # Filter for current month's model
                current_months_data = monthly_data[~monthly_data.index.isin(['2023-05', '2023-06', '2024-07'])]
                
                # Prepare data for current month's linear model
                X_current = current_months_data[investment_columns].values
                y_current = current_months_data[gmv_column].values
                
                # Fit the linear regression model for current months
                model_current = LinearRegression(fit_intercept=True)
                model_current.fit(X_current, y_current)
                
                # Filter for next month's model
                next_months_data = monthly_data[~monthly_data.index.isin(['2023-05', '2023-06', '2023-07'])]
                
                # Calculate next month's GMV ROI
                next_months_data['next_month_gmv'] = next_months_data[gmv_column].shift(-1)
                next_months_data.dropna(subset=['next_month_gmv'], inplace=True)
                
                # Prepare data for next month's linear model
                X_next = next_months_data[investment_columns].values
                y_next = next_months_data['next_month_gmv'].values
                
                # Fit the linear regression model for next month's GMV
                model_next = LinearRegression(fit_intercept=True)
                model_next.fit(X_next, y_next)
                
                # Get model coefficients (impact per dollar spent in each channel)
                channel_coefficients = model_current.coef_
                intercept_current = model_current.intercept_
                channel_coefficients_next = model_next.coef_
                intercept_next = model_next.intercept_
                
                # Calculate total effect (sum of coefficient × investment for all channels)
                current_months_data['total_effect'] = sum(
                    channel_coefficients[i] * current_months_data[channel] 
                    for i, channel in enumerate(channels)
                )
                
                next_months_data['total_effect'] = sum(
                    channel_coefficients_next[i] * next_months_data[channel] 
                    for i, channel in enumerate(channels)
                )
                
                # Calculate attribution for each channel
                for i, channel in enumerate(channels):
                    # For current month
                    current_months_data[f'{channel}_attributed_revenue'] = (
                        (channel_coefficients[i] * current_months_data[channel]* current_months_data[gmv_column]) / 
                        current_months_data['total_effect'] 
                    )

                    current_months_data[f'{channel}_mmm_roi'] = (
                        current_months_data[f'{channel}_attributed_revenue'] 
                    ) / current_months_data[channel]
                    
                    # For next month
                    next_months_data[f'{channel}_attributed_revenue'] = (
                        (channel_coefficients_next[i] * next_months_data[channel]* next_months_data['next_month_gmv']) / 
                        next_months_data['total_effect'] 
                    )

                    next_months_data[f'{channel}_next_month_roi'] = (
                        next_months_data[f'{channel}_attributed_revenue'] 
                    ) / next_months_data[channel]
            
                
                # Calculate overall model fit
                y_pred_current = model_current.predict(X_current)
                y_pred_next = model_next.predict(X_next)
                
                # Generate results
                result += "Marketing Mix Modeling (MMM) Analysis:\n\n"
                
                # Model fit statistics
                result += f"Baseline Revenue (Intercept) (Current Months): ${intercept_current:,.2f} - Revenue expected without marketing\n\n"
                result += f"Baseline Revenue (Intercept) (Next Months): ${intercept_next:,.2f} - Revenue expected without marketing\n\n"
                
                # Channel impact analysis
                result += "Marketing Channel Impact Analysis:\n"
                
                # Sort channels by their coefficient (revenue impact per $ spent)
                sorted_channels_current = sorted([(channel, channel_coefficients[i]) for i, channel in enumerate(channels)], 
                                        key=lambda x: abs(x[1]), reverse=True)
                sorted_channels_next = sorted([(channel, channel_coefficients_next[i]) for i, channel in enumerate(channels)], 
                                        key=lambda x: abs(x[1]), reverse=True)
                
                for channel, coefficient in sorted_channels_current:
                    avg_investment = current_months_data[channel].mean()
                    attr_revenue = current_months_data[f'{channel}_attributed_revenue'].sum()
                    
                    # Use the previously calculated ROI
                    mmm_roi_current = current_months_data[f'{channel}_mmm_roi'].mean()
                    
                    # Calculate attribution percentage
                    attribution_pct_current = (attr_revenue / current_months_data[gmv_column].sum()) * 100
                    
                    result += f"- {channel} (Current Months):\n"
                    result += f"  Impact Coefficient: {coefficient:.4f}\n"
                    result += f"  Average Monthly Investment: ${avg_investment:,.2f}\n"
                    result += f"  Attributed Revenue: ${attr_revenue:,.2f} ({attribution_pct_current:.2f}% of total GMV)\n"
                    result += f"  MMM-based ROI: {mmm_roi_current:.4f}\n"
                    
                    # Add interpretation based on ROI instead of coefficient
                    if mmm_roi_current > 2:
                        result += f"  Very high revenue impact - Each $1 spent generates ${mmm_roi_current:.2f} in revenue\n\n"
                    elif mmm_roi_current > 1:
                        result += f"  Positive revenue impact - Each $1 spent generates ${mmm_roi_current:.2f} in revenue\n\n"
                    elif mmm_roi_current > 0:
                        result += f"  Marginal revenue impact - Each $1 spent generates ${mmm_roi_current:.2f} in revenue\n\n"
                    else:
                        result += f"  Negative revenue impact - Investment in this channel reduces revenue\n\n"
                
                for channel, coefficient in sorted_channels_next:
                    avg_investment = next_months_data[channel].mean()
                    attr_revenue = next_months_data[f'{channel}_attributed_revenue'].sum()
                    
                    # Use the previously calculated ROI
                    mmm_roi_next = next_months_data[f'{channel}_next_month_roi'].mean()
                    
                    # Calculate attribution percentage
                    attribution_pct_next = (attr_revenue / next_months_data[gmv_column].sum()) * 100
                    
                    result += f"- {channel} (Next Months):\n"
                    result += f"  Impact Coefficient: {coefficient:.4f} (revenue $ per investment $)\n"
                    result += f"  Average Monthly Investment: ${avg_investment:,.2f}\n"
                    result += f"  Attributed Revenue: ${attr_revenue:,.2f} ({attribution_pct_next:.2f}% of total GMV)\n"
                    result += f"  MMM-based ROI: {mmm_roi_next:.4f}\n"
                    
                    # Add interpretation based on ROI instead of coefficient
                    if mmm_roi_next > 2:
                        result += f"  Very high revenue impact - Each $1 spent generates ${mmm_roi_next:.2f} in revenue\n\n"
                    elif mmm_roi_next > 1:
                        result += f"  Positive revenue impact - Each $1 spent generates ${mmm_roi_next:.2f} in revenue\n\n"
                    elif mmm_roi_next > 0:
                        result += f"  Marginal revenue impact - Each $1 spent generates ${mmm_roi_next:.2f} in revenue\n\n"
                    else:
                        result += f"  Negative revenue impact - Investment in this channel reduces revenue\n\n"
                
                # Create visualization of channel coefficients (impact per $ spent)
                plt.figure(figsize=(12, 8))
                
                # Get channels and coefficients for plotting
                channels_to_plot_current = [channel for channel, _ in sorted_channels_current]
                channels_to_plot_next = [channel for channel, _ in sorted_channels_next]
                coefficients_to_plot_current = [coef for _, coef in sorted_channels_current]
                coefficients_to_plot_next = [coef for _, coef in sorted_channels_next]
                
                # Create bar chart of coefficients
                plt.bar(channels_to_plot_current, coefficients_to_plot_current)
                plt.bar(channels_to_plot_next, coefficients_to_plot_next)
                plt.axhline(y=1.0, color='red', linestyle='--', label='Break-even line (ROI = 0)')
                plt.xlabel('Marketing Channel')
                plt.ylabel('Revenue Impact Coefficient ($ per $ spent)')
                plt.title('Marketing Channel Impact Coefficients from MMM')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                plt.legend()
                
                # Save figure to buffer
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                
                # Save figure to file with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_filename = f"mmm_channel_impact_{timestamp}.png"
                plot_path = os.path.join(PLOTS_DIR, plot_filename)
                plt.savefig(plot_path)
                plt.close()
                
                logger.info(f"Saved MMM Channel Impact plot to {plot_path}")
                
                # Create visualization of actual vs. predicted GMV
                plt.figure(figsize=(14, 8))
                
                # Plot actual vs. predicted values
                months_current = current_months_data.index.astype(str)
                plt.plot(months_current, current_months_data[gmv_column], 'o-', label='Actual GMV (Current Months)')
                plt.plot(months_current, y_pred_current, 'o--', label='Predicted GMV (Model) - Current Months')
                
                months_next = next_months_data.index.astype(str)
                plt.plot(months_next, next_months_data[gmv_column], 'o-', label='Actual GMV (Next Months)')
                plt.plot(months_next, y_pred_next, 'o--', label='Predicted GMV (Model) - Next Months')
                
                plt.xlabel('Month')
                plt.ylabel('GMV ($)')
                plt.title('Actual vs. Predicted Monthly GMV from Marketing Mix Model')
                plt.xticks(rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Save figure to buffer
                fit_buffer = io.BytesIO()
                plt.savefig(fit_buffer, format='png')
                fit_buffer.seek(0)
                
                # Save figure to file with timestamp
                fit_filename = f"mmm_model_fit_{timestamp}.png"
                fit_path = os.path.join(PLOTS_DIR, fit_filename)
                plt.savefig(fit_path)
                plt.close()
                
                logger.info(f"Saved MMM Model Fit plot to {fit_path}")
                
    
                
                # Create visualization of marginal ROI
                plt.figure(figsize=(12, 8))
                
                # Plot marginal ROI for both current and next months
                x_pos = np.arange(len(channels))
                width = 0.35
                
                # Get marginal ROI values for plotting
                current_marginal_rois = []
                next_marginal_rois = []
                
                for channel in channels:
                    # Current month marginal ROI
                    revenue_change = current_months_data[f'{channel}_attributed_revenue'].diff()
                    investment_change = current_months_data[channel].diff()
                    mask = (investment_change != 0) & (investment_change.notna())
                    marginal_roi = (revenue_change[mask] / investment_change[mask]).mean()  # Take mean here
                    current_marginal_rois.append(marginal_roi)
                    mmm_roi_current = current_months_data[f'{channel}_mmm_roi'].mean()
                    attr_revenue = current_months_data[f'{channel}_attributed_revenue'].sum()
                    attribution_pct_current = (attr_revenue / current_months_data[gmv_column].sum()) * 100
                    
                    # Next month marginal ROI
                    next_revenue_change = next_months_data[f'{channel}_attributed_revenue'].diff()
                    next_investment_change = next_months_data[channel].diff()
                    next_mask = (next_investment_change != 0) & (next_investment_change.notna())
                    marginal_roi_next = (next_revenue_change[next_mask] / next_investment_change[next_mask]).mean()  # Take mean here
                    next_marginal_rois.append(marginal_roi_next)
                    mmm_roi_next = next_months_data[f'{channel}_next_month_roi'].mean()
                    next_month_attr_revenue = next_months_data[f'{channel}_attributed_revenue'].sum()
                    attribution_pct_next = (next_month_attr_revenue / next_months_data[gmv_column].sum()) * 100

                    result += f"\n{channel}:\n"
                    result += f"Current Month Performance:\n"
                    result += f"  Average Marginal ROI: {marginal_roi:.2%} (ΔRevenue/ΔInvestment)\n"
                    
                    result += f"Next Month Performance:\n"
                    result += f"  Projected Average Marginal ROI: {marginal_roi_next:.2%} (ΔRevenue/ΔInvestment)\n"
                    
                    # Updated recommendation logic considering net return
                    result += "  Investment Recommendation: "
                    if attr_revenue > current_months_data[channel].sum() and marginal_roi > 0:
                        if marginal_roi > mmm_roi_current:
                            result += "Strongly increase investment (positive returns with increasing efficiency)\n"
                        else:
                            result += "Moderately increase investment (positive returns but diminishing efficiency)\n"
                    elif attr_revenue > current_months_data[channel].sum():
                        result += "Maintain investment (positive returns but watch marginal efficiency)\n"
                    elif marginal_roi > 0:
                        result += "Consider tactical increases in specific periods (positive marginal returns)\n"
                    else:
                        result += "Consider decreasing investment (negative returns and efficiency)\n"
                
            
                
                # Create the bar plot
                plt.bar(x_pos - width/2, current_marginal_rois, width, 
                       label='Current Months Marginal ROI', color='skyblue')
                plt.bar(x_pos + width/2, next_marginal_rois, width, 
                       label='Next Months Marginal ROI', color='lightgreen')
                
                # Add reference line for break-even point
                plt.axhline(y=0, color='red', linestyle='--', label='Break-even line')
                
                # Customize the plot
                plt.xlabel('Marketing Channel')
                plt.ylabel('Marginal ROI (ΔRevenue/ΔInvestment)')
                plt.title('Marginal ROI Analysis by Channel')
                plt.xticks(x_pos, channels, rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Adjust layout to prevent label cutoff
                plt.tight_layout()
                
                # Save figure to buffer
                marginal_roi_buffer = io.BytesIO()
                plt.savefig(marginal_roi_buffer, format='png')
                marginal_roi_buffer.seek(0)
                
                # Save figure to file with timestamp
                marginal_roi_filename = f"marginal_roi_analysis_{timestamp}.png"
                marginal_roi_path = os.path.join(PLOTS_DIR, marginal_roi_filename)
                plt.savefig(marginal_roi_path)
                plt.close()
                
                logger.info(f"Saved Marginal ROI Analysis plot to {marginal_roi_path}")
                
                # Add path to result
                result += f"Marginal ROI Analysis plot saved to: {marginal_roi_path}\n\n"
                
                # Create visualization of next month ROI using marginal change
                plt.figure(figsize=(12, 8))
                
                # Plot next month marginal ROI
                plt.bar(x_pos, next_marginal_rois, width, label='Next Months Marginal ROI', color='lightgreen')
                
                # Add reference line for break-even point
                plt.axhline(y=0, color='red', linestyle='--', label='Break-even line')
                
                # Customize the plot
                plt.xlabel('Marketing Channel')
                plt.ylabel('Next Month Marginal ROI (ΔRevenue/ΔInvestment)')
                plt.title('Next Month Marginal ROI Analysis by Channel')
                plt.xticks(x_pos, channels, rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Adjust layout to prevent label cutoff
                plt.tight_layout()
                
                # Save figure to buffer
                next_marginal_roi_buffer = io.BytesIO()
                plt.savefig(next_marginal_roi_buffer, format='png')
                next_marginal_roi_buffer.seek(0)
                
                # Save figure to file with timestamp
                next_marginal_roi_filename = f"next_month_marginal_roi_analysis_{timestamp}.png"
                next_marginal_roi_path = os.path.join(PLOTS_DIR, next_marginal_roi_filename)
                plt.savefig(next_marginal_roi_path)
                plt.close()
                
                logger.info(f"Saved Next Month Marginal ROI Analysis plot to {next_marginal_roi_path}")
                
                
                
                # Calculate and format results for each channel
                result += "Channel ROI Insights:\n\n"
                
                # Get high performing channels (coefficient > 1 means positive ROI)
                high_performing_current = [(channel, coef) for channel, coef in sorted_channels_current if coef > 1]
                low_performing_current = [(channel, coef) for channel, coef in sorted_channels_current if coef <= 1]
                high_performing_next = [(channel, coef) for channel, coef in sorted_channels_next if coef > 1]
                low_performing_next = [(channel, coef) for channel, coef in sorted_channels_next if coef <= 1]
                
                if high_performing_current:
                    result += f"1. Increase investment in high-performing channels (Current Months): {', '.join([channel for channel, _ in high_performing_current])}\n"
                    result += "   These channels generate more revenue than their cost, providing positive ROI\n"
                
                if low_performing_current:
                    result += f"2. Reduce investment in low-performing channels (Current Months): {', '.join([channel for channel, _ in low_performing_current])}\n"
                    result += "   These channels generate less revenue than their cost, providing negative or minimal ROI\n"
                
                if high_performing_next:
                    result += f"3. Increase investment in high-performing channels (Next Months): {', '.join([channel for channel, _ in high_performing_next])}\n"
                    result += "   These channels generate more revenue than their cost, providing positive ROI\n"
                
                if low_performing_next:
                    result += f"4. Reduce investment in low-performing channels (Next Months): {', '.join([channel for channel, _ in low_performing_next])}\n"
                    result += "   These channels generate less revenue than their cost, providing negative or minimal ROI\n"
                
                
                # Strategic recommendations
                result += "\nStrategic Recommendations:\n"
                
                if high_performing_current or high_performing_next:
                    result += "1. Prioritize customer satisfaction initiatives as they significantly impact future ROI\n"
                    result += "2. Set minimum monthly ROI targets based on the observed relationship with GMV\n"
                    if high_performing_current:
                        result += f"3. Aim for ROI above {mmm_roi_current:.2f} for high-performing channels (Current Months)\n"
                    if high_performing_next:
                        result += f"4. Aim for ROI above {mmm_roi_next:.2f} for high-performing channels (Next Months)\n"
                else:
                    result += "1. Investigate why customer satisfaction isn't strongly translating to improved ROI\n"
                    result += "2. Identify other factors beyond ROI that may be stronger drivers of GMV\n"
                    result += "3. Review marketing investment allocation to ensure budget is directed to highest ROI channels\n"
                    result += "4. Consider developing a more sophisticated customer satisfaction metric beyond ROI\n"
                
                result += "6. Implement a monthly ROI-to-GMV tracking system to monitor how this relationship evolves over time\n"
                
                logger.info(f"calculate_channel_roi with MMM completed for {table_name}")
                logger.info("Results: ")
                logger.info(result)
                return result
                
            except Exception as e:
                error_msg = f"Error in MMM channel ROI analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def nps_roi_analysis(table_name: str = "Master", nps_column: str = "NPS_Score", 
                             date_column: str = "order_date", gmv_column: str = "gmv", 
                             investment_column: str = "Total Investment") -> str:
            """
            Analyze the relationship between average monthly NPS scores and next month's ROI.
            
            Args:
                table_name: Name of the table containing NPS and ROI data
                nps_column: Column name with NPS scores
                date_column: Column name with date information
                gmv_column: Column name with GMV data
                investment_column: Column name with total investment data
                
            Returns:
                String with NPS and ROI analysis results
            """
            logger.info(f"Tool called: nps_roi_analysis")
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name].copy()
                
                # Ensure required columns exist
                required_columns = [nps_column, date_column, gmv_column, investment_column]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return f"Columns not found: {missing_columns}. Available columns: {', '.join(df.columns)}"
                
                # Convert date column to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                    df[date_column] = pd.to_datetime(df[date_column])
                
                # Create year-month column for aggregation
                df['year_month'] = df[date_column].dt.to_period('M')
                
                # Group by month to get monthly NPS, GMV, and investment
                monthly_data = df.groupby('year_month').agg({
                    nps_column: 'mean',
                    gmv_column: 'sum',
                    investment_column: 'mean'  # Assuming investment is already monthly
                })
                
                # Calculate current month's ROI: Monthly GMV / Monthly Investment
                monthly_data['current_roi'] = monthly_data[gmv_column] / monthly_data[investment_column]
                
                # Calculate next month's GMV, investment and ROI
                monthly_data['next_month_gmv'] = monthly_data[gmv_column].shift(-1)
                monthly_data['next_month_investment'] = monthly_data[investment_column].shift(-1)
                monthly_data['next_month_roi'] = monthly_data['next_month_gmv'] / monthly_data['next_month_investment']
                
                # Drop the last row as it won't have next month's data
                monthly_data = monthly_data.dropna(subset=['next_month_roi'])
                
                # Calculate correlation between current month's NPS and next month's ROI
                correlation_nps_roi = monthly_data[nps_column].corr(monthly_data['next_month_roi'])
                
                # Generate results
                result = "NPS vs Next Month's ROI Analysis:\n\n"
                
                # Overall stats
                avg_nps = monthly_data[nps_column].mean()
                avg_roi = monthly_data['current_roi'].mean()
                avg_next_roi = monthly_data['next_month_roi'].mean()
                
                result += f"Average Monthly NPS Score: {avg_nps:.2f}\n"
                result += f"Correlation between NPS and Next Month's ROI: {correlation_nps_roi:.4f}\n\n"
                
                # Month by month analysis
                result += "Monthly NPS and ROI Trends:\n"
                
                # Convert Period index to string for better display
                monthly_data_display = monthly_data.copy()
                monthly_data_display.index = monthly_data_display.index.astype(str)
                
                # Sort by correlation strength
                months = monthly_data_display.index.tolist()
                
                for month in months:
                    result += f"- {month}:\n"
                    
                    # Calculate month-over-month changes
                    if month != months[0]:  # Skip for the first month
                        prev_month = months[months.index(month) - 1]
                        nps_change = (monthly_data_display.loc[month, nps_column] - 
                                    monthly_data_display.loc[prev_month, nps_column])
                        roi_change = (monthly_data_display.loc[month, 'next_month_roi'] - 
                                     monthly_data_display.loc[prev_month, 'next_month_roi'])
                        
                        nps_change_str = f"increased by {nps_change:.2f}" if nps_change >= 0 else f"decreased by {abs(nps_change):.2f}"
                        roi_change_str = f"increased by {roi_change:.2f}" if roi_change >= 0 else f"decreased by {abs(roi_change):.2f}"
                        
                        result += f"  NPS {nps_change_str} from previous month\n"
                        result += f"  Next Month ROI {roi_change_str} from previous month\n"
                    
                    result += "\n"
                
                # Create scatter plot of NPS vs next month's ROI
                plt.figure(figsize=(12, 8))
                
                # Plot NPS vs next month's ROI
                plt.scatter(monthly_data[nps_column], monthly_data['next_month_roi'], s=100, alpha=0.7)
                
                # Add month labels to each point
                for i, month in enumerate(monthly_data.index):
                    plt.annotate(
                        month.strftime('%Y-%m'), 
                        (monthly_data.iloc[i][nps_column], monthly_data.iloc[i]['next_month_roi']),
                        xytext=(5, 5),
                        textcoords='offset points'
                    )
                
                # Add trend line
                z = np.polyfit(monthly_data[nps_column], monthly_data['next_month_roi'], 1)
                p = np.poly1d(z)
                plt.plot(monthly_data[nps_column], p(monthly_data[nps_column]), "r--", alpha=0.8, 
                        label=f'Trend (r={correlation_nps_roi:.2f})')
                
                plt.xlabel('Monthly Average NPS Score')
                plt.ylabel('Next Month ROI')
                plt.title('Monthly NPS Score vs Next Month ROI')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Save figure to buffer
                scatter_buffer = io.BytesIO()
                plt.savefig(scatter_buffer, format='png')
                scatter_buffer.seek(0)
                
                # Save figure to file with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                scatter_filename = f"nps_roi_scatter_{timestamp}.png"
                scatter_path = os.path.join(PLOTS_DIR, scatter_filename)
                plt.savefig(scatter_path)
                plt.close()
                
                logger.info(f"Saved NPS vs ROI scatter plot to {scatter_path}")
                
                # Create time series plot of NPS and next month's ROI
                plt.figure(figsize=(14, 10))
                
                # Create a line for NPS (on left y-axis)
                ax1 = plt.gca()
                ax2 = ax1.twinx()
                
                # Plot NPS scores (on left y-axis)
                ax1.plot(monthly_data.index.astype(str), monthly_data[nps_column], 
                       marker='o', color='blue', label='Monthly NPS Score')
                
                # Plot next month's ROI (on right y-axis)
                ax2.plot(monthly_data.index.astype(str), monthly_data['next_month_roi'], 
                        marker='s', color='green', label='Next Month ROI')
                
                # Set labels and title
                ax1.set_xlabel('Month')
                ax1.set_ylabel('NPS Score')
                ax2.set_ylabel('Next Month ROI')
                plt.title('Monthly NPS Score vs Next Month ROI Over Time')
                
                # Combine legends from both axes
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save figure to buffer
                timeseries_buffer = io.BytesIO()
                plt.savefig(timeseries_buffer, format='png')
                timeseries_buffer.seek(0)
                
                # Save figure to file with timestamp
                timeseries_filename = f"nps_roi_timeseries_{timestamp}.png"
                timeseries_path = os.path.join(PLOTS_DIR, timeseries_filename)
                plt.savefig(timeseries_path)
                plt.close()
                
                logger.info(f"Saved NPS vs ROI time series plot to {timeseries_path}")
                
                
                # Identify months with highest and lowest NPS
                high_nps_month = monthly_data[nps_column].idxmax()
                low_nps_month = monthly_data[nps_column].idxmin()
                
                high_nps_next_roi = monthly_data.loc[high_nps_month, 'next_month_roi']
                low_nps_next_roi = monthly_data.loc[low_nps_month, 'next_month_roi']
                
                # Add key insights
                result += "Key Insights:\n"
                result += f"1. The correlation between monthly NPS and next month's ROI is {correlation_nps_roi:.4f}, "
                
                if correlation_nps_roi > 0.7:
                    result += "indicating a strong positive relationship. Higher customer satisfaction strongly predicts better ROI in the following month.\n"
                elif correlation_nps_roi > 0.3:
                    result += "indicating a moderate positive relationship. Higher customer satisfaction tends to predict better ROI in the following month.\n"
                elif correlation_nps_roi > 0:
                    result += "indicating a weak positive relationship. Higher customer satisfaction may slightly predict better ROI in the following month.\n"
                elif correlation_nps_roi > -0.3:
                    result += "indicating a weak negative relationship. Higher customer satisfaction counter-intuitively predicts slightly lower ROI in the following month.\n"
                else:
                    result += "indicating a strong negative relationship. Higher customer satisfaction counter-intuitively predicts lower ROI in the following month.\n"
                
                # Month with highest NPS
                result += f"2. The month with highest NPS ({high_nps_month.strftime('%Y-%m')}, NPS: {monthly_data.loc[high_nps_month, nps_column]:.2f}) "
                result += f"was followed by a month with ROI of {high_nps_next_roi:.2f}\n"
                
                # Month with lowest NPS
                result += f"3. The month with lowest NPS ({low_nps_month.strftime('%Y-%m')}, NPS: {monthly_data.loc[low_nps_month, nps_column]:.2f}) "
                result += f"was followed by a month with ROI of {low_nps_next_roi:.2f}\n"
                
                # Calculate average NPS threshold for good ROI
                if correlation_nps_roi > 0.3:  # Only meaningful if there's a decent correlation
                    high_roi_threshold = monthly_data['next_month_roi'].quantile(0.75)
                    high_roi_months = monthly_data[monthly_data['next_month_roi'] >= high_roi_threshold]
                    if not high_roi_months.empty:
                        avg_nps_for_high_roi = high_roi_months[nps_column].mean()
                        result += f"4. Months with an NPS score of {avg_nps_for_high_roi:.2f} or higher tend to be followed by months with top 25% ROI performance\n"
                
                # Add trend analysis
                if len(monthly_data) >= 3:
                    recent_nps_trend = monthly_data[nps_column].iloc[-3:].pct_change().mean() * 100
                    recent_roi_trend = monthly_data['next_month_roi'].iloc[-3:].pct_change().mean() * 100
                    
                    result += "5. Recent trends:\n"
                    
                    nps_trend_str = "increasing" if recent_nps_trend > 0 else "decreasing"
                    roi_trend_str = "increasing" if recent_roi_trend > 0 else "decreasing"
                    
                    result += f"   - NPS scores have been {nps_trend_str} by {abs(recent_nps_trend):.1f}% per month recently\n"
                    result += f"   - Next month ROI has been {roi_trend_str} by {abs(recent_roi_trend):.1f}% per month recently\n"
                
                # Strategic recommendations
                result += "\nStrategic Recommendations:\n"
                
                if correlation_nps_roi > 0.3:
                    result += "1. Prioritize customer satisfaction initiatives as they significantly impact future ROI\n"
                    result += "2. Set minimum monthly NPS targets based on the observed relationship with ROI\n"
                    result += f"3. Aim for NPS scores above {avg_nps:.2f} to maintain or improve current ROI performance\n"
                    if 'avg_nps_for_high_roi' in locals():
                        result += f"4. Implement targeted programs to achieve NPS scores of {avg_nps_for_high_roi:.2f} or higher to maximize ROI\n"
                else:
                    result += "1. Investigate why customer satisfaction isn't strongly translating to improved ROI\n"
                    result += "2. Identify other factors beyond NPS that may be stronger drivers of next month's ROI\n"
                    result += "3. Review marketing investment allocation to ensure budget is directed to highest ROI channels\n"
                    result += "4. Consider developing a more sophisticated customer satisfaction metric beyond NPS\n"
                
                
                logger.info(f"nps_roi_analysis completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error in NPS vs ROI analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
                
        def stock_index_roi_analysis(table_name: str = "Master", stock_index_column: str = "Stock_Index", 
                                   date_column: str = "order_date", gmv_column: str = "gmv", 
                                   investment_column: str = "Total Investment") -> str:
            """
            Analyze the relationship between average monthly stock index and current monthly ROI.
            
            Args:
                table_name: Name of the table containing stock index and ROI data
                stock_index_column: Column name with stock index values
                date_column: Column name with date information
                gmv_column: Column name with GMV data
                investment_column: Column name with total investment data
                
            Returns:
                String with stock index and ROI analysis results
            """
            logger.info(f"Tool called: stock_index_roi_analysis")
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name].copy()
                
                # Ensure required columns exist
                required_columns = [stock_index_column, date_column, gmv_column, investment_column]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return f"Columns not found: {missing_columns}. Available columns: {', '.join(df.columns)}"
                
                # Convert date column to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                    df[date_column] = pd.to_datetime(df[date_column])
                
                # Create year-month column for aggregation
                df['year_month'] = df[date_column].dt.to_period('M')
                
                # Group by month to get monthly stock index, GMV, and investment
                monthly_data = df.groupby('year_month').agg({
                    stock_index_column: 'mean',
                    gmv_column: 'sum',
                    investment_column: 'mean'  # Assuming investment is already monthly
                })
                
                # Calculate current month's ROI: Monthly GMV / Monthly Investment
                monthly_data['current_roi'] = monthly_data[gmv_column] / monthly_data[investment_column]
                
                # Calculate next month's ROI for additional analysis
                monthly_data['next_month_gmv'] = monthly_data[gmv_column].shift(-1)
                monthly_data['next_month_investment'] = monthly_data[investment_column].shift(-1)
                monthly_data['next_month_roi'] = monthly_data['next_month_gmv'] / monthly_data['next_month_investment']
                
                # Calculate month-over-month changes
                monthly_data['stock_index_change_pct'] = monthly_data[stock_index_column].pct_change() * 100
                monthly_data['roi_change_pct'] = monthly_data['current_roi'].pct_change() * 100
                
                # Calculate correlation between stock index and ROI
                correlation_stock_roi = monthly_data[stock_index_column].corr(monthly_data['current_roi'])
                
                # Calculate correlation between stock index change and ROI change
                correlation_stock_change_roi_change = monthly_data['stock_index_change_pct'].corr(monthly_data['roi_change_pct'])
                
                # Generate results
                result = "Stock Index vs Current Month ROI Analysis:\n\n"
                
                # Overall stats
                avg_stock_index = monthly_data[stock_index_column].mean()
                avg_roi = monthly_data['current_roi'].mean()
                
                result += f"Average Monthly Stock Index: {avg_stock_index:.2f}\n"
                result += f"Correlation between Stock Index and Current Month ROI: {correlation_stock_roi:.4f}\n"
                result += f"Correlation between Stock Index % Change and ROI % Change: {correlation_stock_change_roi_change:.4f}\n\n"
                
                # Month by month analysis
                result += "Monthly Stock Index and ROI Trends:\n"
                
                # Convert Period index to string for better display
                monthly_data_display = monthly_data.copy()
                monthly_data_display.index = monthly_data_display.index.astype(str)
                
                # Sort by date (which is the index)
                months = monthly_data_display.index.tolist()
                
                for month in months:
                    result += f"- {month}:\n"
                    
                    # Add month-over-month changes if not the first month
                    if month != months[0]:
                        stock_change = monthly_data_display.loc[month, 'stock_index_change_pct']
                        roi_change = monthly_data_display.loc[month, 'roi_change_pct']
                        
                        stock_change_str = f"increased by {stock_change:.2f}%" if stock_change >= 0 else f"decreased by {abs(stock_change):.2f}%"
                        roi_change_str = f"increased by {roi_change:.2f}%" if roi_change >= 0 else f"decreased by {abs(roi_change):.2f}%"
                        
                        result += f"  Stock Index {stock_change_str} from previous month\n"
                        result += f"  ROI {roi_change_str} from previous month\n"
                    
                    result += "\n"
                
                # Create scatter plot of Stock Index vs ROI
                plt.figure(figsize=(12, 8))
                    
                # Plot Stock Index vs current month ROI
                plt.scatter(monthly_data[stock_index_column], monthly_data['current_roi'], s=100, alpha=0.7)
                
                # Add month labels to each point
                for i, month in enumerate(monthly_data.index):
                    plt.annotate(
                        month.strftime('%Y-%m'), 
                        (monthly_data.iloc[i][stock_index_column], monthly_data.iloc[i]['current_roi']),
                        xytext=(5, 5),
                        textcoords='offset points'
                    )
                
                # Add trend line
                z = np.polyfit(monthly_data[stock_index_column], monthly_data['current_roi'], 1)
                p = np.poly1d(z)
                plt.plot(monthly_data[stock_index_column], p(monthly_data[stock_index_column]), "r--", alpha=0.8, 
                        label=f'Trend (r={correlation_stock_roi:.2f})')
                
                plt.xlabel('Monthly Average Stock Index')
                plt.ylabel('Current Month ROI')
                plt.title('Monthly Stock Index vs Current Month ROI')
                plt.legend()
                plt.grid(True, alpha=0.3)
                    
                # Save figure to buffer
                scatter_buffer = io.BytesIO()
                plt.savefig(scatter_buffer, format='png')
                scatter_buffer.seek(0)
                
                # Save figure to file with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                scatter_filename = f"stock_roi_scatter_{timestamp}.png"
                scatter_path = os.path.join(PLOTS_DIR, scatter_filename)
                plt.savefig(scatter_path)
                plt.close()
                
                logger.info(f"Saved Stock Index vs ROI scatter plot to {scatter_path}")
                
                # Create time series plot of Stock Index and ROI
                plt.figure(figsize=(14, 10))
                
                # Create a line for Stock Index (on left y-axis)
                ax1 = plt.gca()
                ax2 = ax1.twinx()
                
                # Plot Stock Index (on left y-axis)
                ax1.plot(monthly_data.index.astype(str), monthly_data[stock_index_column], 
                       marker='o', color='blue', label='Stock Index')
                
                # Plot current month ROI (on right y-axis)
                ax2.plot(monthly_data.index.astype(str), monthly_data['current_roi'], 
                        marker='s', color='green', label='Current Month ROI')
                
                # Set labels and title
                ax1.set_xlabel('Month')
                ax1.set_ylabel('Stock Index')
                ax2.set_ylabel('Current Month ROI')
                plt.title('Monthly Stock Index vs Current Month ROI Over Time')
                
                # Combine legends from both axes
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save figure to buffer
                timeseries_buffer = io.BytesIO()
                plt.savefig(timeseries_buffer, format='png')
                timeseries_buffer.seek(0)
                
                # Save figure to file with timestamp
                timeseries_filename = f"stock_roi_timeseries_{timestamp}.png"
                timeseries_path = os.path.join(PLOTS_DIR, timeseries_filename)
                plt.savefig(timeseries_path)
                plt.close()
                
                logger.info(f"Saved Stock Index vs ROI time series plot to {timeseries_path}")
                
                
                # Identify months with highest and lowest stock index
                high_stock_month = monthly_data[stock_index_column].idxmax()
                low_stock_month = monthly_data[stock_index_column].idxmin()
                
                high_stock_roi = monthly_data.loc[high_stock_month, 'current_roi']
                low_stock_roi = monthly_data.loc[low_stock_month, 'current_roi']
                
                # Add key insights
                result += "Key Insights:\n"
                result += f"1. The correlation between monthly Stock Index and Current Month ROI is {correlation_stock_roi:.4f}, "
                
                if correlation_stock_roi > 0.7:
                    result += "indicating a strong positive relationship. Higher stock index strongly correlates with better ROI.\n"
                elif correlation_stock_roi > 0.3:
                    result += "indicating a moderate positive relationship. Higher stock index tends to correlate with better ROI.\n"
                elif correlation_stock_roi > 0:
                    result += "indicating a weak positive relationship. Higher stock index may slightly correlate with better ROI.\n"
                elif correlation_stock_roi > -0.3:
                    result += "indicating a weak negative relationship. Higher stock index counter-intuitively correlates with slightly lower ROI.\n"
                else:
                    result += "indicating a strong negative relationship. Higher stock index counter-intuitively correlates with lower ROI.\n"
                
                # Month with highest stock index
                result += f"2. The month with highest stock index ({high_stock_month.strftime('%Y-%m')}, Index: {monthly_data.loc[high_stock_month, stock_index_column]:.2f}) "
                result += f"had a ROI of {high_stock_roi:.2f}\n"
                
                # Month with lowest stock index
                result += f"3. The month with lowest stock index ({low_stock_month.strftime('%Y-%m')}, Index: {monthly_data.loc[low_stock_month, stock_index_column]:.2f}) "
                result += f"had a ROI of {low_stock_roi:.2f}\n"
                
                # Calculate average ROI during market uptrends vs downtrends
                if len(monthly_data) >= 3:
                    # Identify uptrend and downtrend months
                    monthly_data['is_uptrend'] = monthly_data[stock_index_column].pct_change() > 0
                    uptrend_months = monthly_data[monthly_data['is_uptrend'] == True]
                    downtrend_months = monthly_data[monthly_data['is_uptrend'] == False]
                    
                    if not uptrend_months.empty and not downtrend_months.empty:
                        avg_roi_uptrend = uptrend_months['current_roi'].mean()
                        avg_roi_downtrend = downtrend_months['current_roi'].mean()
                        
                        result += f"4. Average ROI during stock market uptrends: {avg_roi_uptrend:.2f}\n"
                        result += f"5. Average ROI during stock market downtrends: {avg_roi_downtrend:.2f}\n"
                        
                        # Calculate difference
                        pct_diff = ((avg_roi_uptrend / avg_roi_downtrend) - 1) * 100 if avg_roi_downtrend > 0 else 0
                        if pct_diff != 0:
                            result += f"6. ROI during uptrends is {abs(pct_diff):.1f}% {'higher' if pct_diff > 0 else 'lower'} than during downtrends\n"
                
                # Add trend analysis
                if len(monthly_data) >= 3:
                    recent_stock_trend = monthly_data[stock_index_column].iloc[-3:].pct_change().mean() * 100
                    recent_roi_trend = monthly_data['current_roi'].iloc[-3:].pct_change().mean() * 100
                    
                    result += "7. Recent trends:\n"
                    
                    stock_trend_str = "increasing" if recent_stock_trend > 0 else "decreasing"
                    roi_trend_str = "increasing" if recent_roi_trend > 0 else "decreasing"
                    
                    result += f"   - Stock index has been {stock_trend_str} by {abs(recent_stock_trend):.1f}% per month recently\n"
                    result += f"   - ROI has been {roi_trend_str} by {abs(recent_roi_trend):.1f}% per month recently\n"
                
                # Calculate lag effect (stock index leading indicator of ROI?)
                lag_correlation = monthly_data[stock_index_column].corr(monthly_data['next_month_roi'])
                result += f"8. Correlation between current month Stock Index and next month's ROI: {lag_correlation:.4f}\n"
                
                if abs(lag_correlation) > abs(correlation_stock_roi):
                    result += "   This suggests stock index may be a leading indicator for ROI\n"
                
                # Strategic recommendations
                result += "\nStrategic Recommendations:\n"
                
                if correlation_stock_roi > 0.3 or lag_correlation > 0.3:
                    result += "1. Monitor stock market trends as a potential indicator for marketing ROI performance\n"
                    result += "2. Consider adjusting marketing investment strategy based on stock market conditions\n"
                    
                    if lag_correlation > 0.3:
                        result += "3. Use stock index as a predictive indicator for next month's expected ROI\n"
                        
                    if abs(pct_diff) > 10 and 'avg_roi_uptrend' in locals() and 'avg_roi_downtrend' in locals():
                        if avg_roi_uptrend > avg_roi_downtrend:
                            result += "4. Consider increasing marketing investments during stock market uptrends\n"
                            result += "5. Be more selective with marketing spend during market downtrends\n"
                        else:
                            result += "4. Marketing ROI performs better during market downtrends, possibly due to lower competition\n"
                            result += "5. Consider maintaining or increasing marketing investments during market downtrends\n"
                else:
                    result += "1. Stock index does not show a strong relationship with marketing ROI\n"
                    result += "2. Focus on other factors that may have stronger influence on marketing effectiveness\n"
                    result += "3. Consider a more detailed analysis to identify market factors that do correlate with ROI\n"
                
                logger.info(f"stock_index_roi_analysis completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error in Stock Index vs ROI analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        # Create tools list
        return [
            StructuredTool.from_function(
                func=calculate_channel_roi,
                name="calculate_channel_roi",
                description="Calculate ROI metrics for different marketing channels"
            ),
            StructuredTool.from_function(
                func=nps_roi_analysis,
                name="nps_roi_analysis",
                description="Analyze the relationship between average monthly NPS scores and next month's ROI"
            ),
            StructuredTool.from_function(
                func=stock_index_roi_analysis,
                name="stock_index_roi_analysis",
                description="Analyze the relationship between average monthly stock index and current monthly ROI"
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ROI analysis agent."""
        logger.info("Creating ROI analysis agent")
        
        # Get data schema
        data_schema = self._get_data_schema()
        
        # Use a simpler prompt for faster parsing and generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a marketing ROI data generator. Your task is to extract ROI data using the tools provided and give it in the output without processing as it is.
            
            Here is the schema of the available data: {data_schema}

            ONLY USE THE TABLES EXACTLY GIVEN IN THE DATA SCHEMA AND USE THE COLUMN NAMES EXACTLY AS THEY ARE IN THE DATA SCHEMA
            
            You have access to marketing data and can use the following tools:
            - calculate_channel_roi: Analyze how different marketing channels affect next month's GMV
            - nps_roi_analysis: Analyze the relationship between average monthly NPS scores and next month's ROI
            - stock_index_roi_analysis: Analyze the relationship between average monthly stock index and current monthly ROI
            
            IMPORTANT: In your final response, be sure to include the values(numerics) of:
            
            1. From calculate_channel_roi:
               - Channel impact coefficients for each marketing channel (current and next months)
               - Attributed revenue and attribution percentages for each channel
               - Baseline Revenue (Intercept) for both Current and Next Months
               - MMM-based ROI for each marketing channel
               - Marginal ROI values for each channel
               - All visualizations paths (plot_path values)
               
            2. From nps_roi_analysis:
               - Correlation between NPS and Next Month's ROI
               - Average Monthly NPS Score
               - Month with highest NPS and its next month ROI
               - Month with lowest NPS and its next month ROI
               - All visualizations paths (plot_path values)
               
            3. From stock_index_roi_analysis:
               - Correlation between Stock Index and Current Month ROI
               - Correlation between Stock Index % Change and ROI % Change
               - Average Monthly Stock Index
               - Month with highest stock index and its ROI
               - Month with lowest stock index and its ROI
               - Average ROI during stock market uptrends and downtrends
               - All visualizations paths (plot_path values)
               
            NOTE:
            
            1. Complete numerical data from all analyses you run (correlations, averages, ranges, etc.)
            2. All key statistical insights (include exact numbers with proper formatting)
            
            Your final response must be detailed and data-rich.
            Include ALL relevant data points, statistics, and findings from your analysis tools in a structured format.
            Do not summarize or omit specific numerical values - include the complete data outputs.
            
            Report all values exactly as returned from the tools, preserving all decimal places and formatting.
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(
            self.llm,
            self.tools,
            prompt
        )
        
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
    
    def invoke(self, query: str) -> str:
        """
        Analyze marketing ROI based on the query.
        
        Args:
            query: Analysis question to be answered
            
        Returns:
            str: Analysis results
        """
        logger.info(f"Analyzing ROI query: {query}")
        
        # Create agent executor if it hasn't been created yet
        if not self.agent_executor:
            logger.info("Creating agent executor for first use")
            self.agent_executor = self._create_agent()
        
        max_attempts = 2  # Reduced from 3 to 2 to minimize API calls
        attempt = 0
        
        while attempt < max_attempts:
            try:
                result = self.agent_executor.invoke({"input": query})
                logger.info("ROI analysis completed successfully")
                return result["output"]
            except Exception as e:
                attempt += 1
                error_msg = f"Error in ROI analysis (attempt {attempt}/{max_attempts}): {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
                if attempt < max_attempts:
                    # Use shorter wait times between retries
                    wait_time = 5 * attempt
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Error in ROI analysis after {max_attempts} attempts: {str(e)}"

def get_roi_agent(llm=None, data_manager=None, quick_mode=False):
    """Create a ROI analysis agent."""
    logger.info("Creating ROI agent")
    
    # Set default data directory to the 'data' folder in the project
    if data_manager is None:
        # Get the directory containing the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to project root and then into 'data' folder
        data_dir = os.path.join(os.path.dirname(script_dir), "data")
        logger.info(f"Using default data directory: {data_dir}")
        
        # If data directory doesn't exist, try looking for it in the current directory
        if not os.path.exists(data_dir):
            data_dir = os.path.join(script_dir, "data")
            logger.info(f"Default data directory not found, trying: {data_dir}")
            
            # If still not found, create an empty data directory
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                logger.info(f"Created empty data directory at: {data_dir}")
                print(f"Created empty data directory at: {data_dir}")
                print("Please add CSV files to this directory before running analyses.")
    
    if llm is None:
        try:
            # Try to get API key from environment variable first
            api_key = os.environ.get("GROQ_API_KEY")
            
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            # Select model based on quick_mode preference
            if quick_mode:
                model = "llama-3.1-8b-instant"  # Fastest model for quick responses
                timeout = 30
                request_timeout = 15
                logger.info("Using fast model for quick analysis")
            else:
                model = "llama-3.3-70b-versatile"  # More capable model for detailed analysis
                timeout = 60
                request_timeout = 30
                logger.info("Using standard model for detailed analysis")
            
            # Optimize API configuration
            llm = ChatGroq(
                api_key=api_key,
                model=model,
                temperature=0,                # Deterministic outputs
                max_retries=3,                # Reasonable retry amount
                timeout=timeout,              # Overall timeout
                request_timeout=request_timeout # Specific request timeout
            )
            logger.info(f"Successfully initialized Groq LLM with model: {model}")
        except Exception as e:
            logger.error(f"Error initializing Groq LLM: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to initialize language model: {str(e)}")
    
    try:
        # Create the ROI agent
        agent = ROIAgent(llm, data_manager)
        return agent
    except Exception as e:
        logger.error(f"Error creating ROI agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to create ROI agent: {str(e)}")

def main():
    """Main function to run the ROI analysis."""
    print("\nInitializing ROI Analysis Agent...")
    print("="*80)
    
    try:
        # Ask if user wants to run in quick mode
        quick_mode = input("\nDo you want to run in quick mode with faster analyses? (y/n): ").lower().startswith('y')
        
        if quick_mode:
            print("\nRunning in quick mode with faster model and minimal waiting times.")
        
        # Initialize the agent with quick_mode setting - but don't create the agent executor yet
        # This will just load the data and tools without making any API calls
        agent = get_roi_agent(quick_mode=quick_mode)
        
        # Print information about plots directory
        print(f"\nPlots will be saved to: {PLOTS_DIR}")
        print("You can view the generated plots in this directory after each analysis.")
        
        # Access to direct function execution to avoid agent overhead for simple requests
        tools_dict = {tool.name: tool.func for tool in agent.tools}
        
        while True:
            print("\nROI Analysis Options:")
            print("1. Analyze marketing channels' effect on next month's GMV")
            print("2. Analyze the relationship between average monthly NPS scores and next month's ROI")
            print("3. Analyze the relationship between stock index and current monthly ROI")
            print("4. Run All Analyses")
            print("5. Extract Monthly ROI Metrics")
            print("6. Custom Analysis Query")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ")
            
            try:
                start_time = time.time()
                
                # Direct function execution for standard analyses to avoid API calls
                if choice == '1':
                    print("\nAnalyzing marketing channels... Please wait...")
                    # Direct function call instead of using the agent
                    result = tools_dict["calculate_channel_roi"]()
                    print("\nResults:")
                    print(result)
                
                elif choice == '2':
                    print("\nAnalyzing NPS and ROI relationship... Please wait...")
                    # Direct function call instead of using the agent
                    result = tools_dict["nps_roi_analysis"]()
                    print("\nResults:")
                    print(result)
                
                elif choice == '3':
                    print("\nAnalyzing stock index and ROI relationship... Please wait...")
                    # Direct function call instead of using the agent
                    result = tools_dict["stock_index_roi_analysis"]()
                    print("\nResults:")
                    print(result)
                
                elif choice == '4':
                    run_all_analyses(agent, quick_mode=quick_mode)
                
                elif choice == '5':
                    print("\nExtracting monthly ROI metrics... Please wait...")
                    export_json = input("Export results to JSON? (y/n): ").lower().startswith('y')
                    
                    # Call the extract_monthly_roi_metrics function
                    result = extract_monthly_roi_metrics(export_json=export_json)
                    
                    # Check if result is a DataFrame or an error message string
                    if isinstance(result, pd.DataFrame):
                        monthly_roi_df = result
                        print("\nMonthly ROI Metrics:")
                        print(monthly_roi_df.to_string(index=False))
                        
                        # Print summary statistics
                        print("\nSummary Statistics:")
                        print(monthly_roi_df.describe())
                        
                        # Calculate month-over-month growth rates
                        print("\nMonth-over-Month Growth Rates:")
                        growth_df = monthly_roi_df.copy()
                        for column in growth_df.columns:
                            if column != 'Month':
                                growth_df[f'{column}_Growth'] = growth_df[column].pct_change() * 100
                        
                        growth_columns = [col for col in growth_df.columns if 'Growth' in col]
                        print(growth_df[['Month'] + growth_columns].to_string(index=False))
                    else:
                        # Print the error message
                        print(f"\nError: {result}")
                
                elif choice == '6':
                    query = input("\nEnter your analysis query: ")
                    print(f"\nProcessing your query... Please wait...")
                    # Only use the agent for custom queries that need LLM reasoning
                    if not agent.agent_executor:
                        print("Initializing AI reasoning capabilities for custom query...")
                        # Only create the agent executor when needed for custom queries
                        agent.agent_executor = agent._create_agent()
                    result = agent.invoke(query)
                    print("\nResults:")
                    print(result)
                
                elif choice == '7':
                    print("\nExiting ROI Analysis Tool...")
                    break
                
                else:
                    print("\nInvalid choice. Please try again.")
                
                # Display execution time for better user feedback
                if choice in ['1', '2', '3', '5', '6']:
                    elapsed_time = time.time() - start_time
                    print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
            
            except Exception as e:
                print(f"\nError during analysis: {str(e)}")
                logger.error(f"Error during menu option {choice}: {str(e)}")
                logger.error(traceback.format_exc())
                print("\nPlease try again or select a different option.")
            
            input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.error(traceback.format_exc())
        return 1
    
    return 0

def run_all_analyses(agent, quick_mode=False):
    """Run all available ROI analyses and print results (legacy function kept for backward compatibility)."""
    # Check if agent.agent_executor exists
    if not agent.agent_executor:
        # If it doesn't exist, use the direct approach instead (preferred)
        tools_dict = {tool.name: tool.func for tool in agent.tools}
        return run_all_analyses_direct(tools_dict, quick_mode=quick_mode)
    
    # Legacy implementation with agent for backward compatibility
    analyses = [
        "Analyze marketing channels' effect on next month's GMV",
        "Analyze the relationship between average monthly NPS scores and next month's ROI",
        "Analyze the relationship between stock index and current monthly ROI"
    ]
    
    for i, analysis in enumerate(analyses):
        print("\n" + "="*80)
        print(f"\nRunning analysis: {analysis}")
        print("="*80 + "\n")
        start_time = time.time()
        
        try:
            print(f"Processing... Please wait...")
            result = agent.invoke(analysis)
            print(result)
            
            # Add shorter delay between analyses to avoid rate limiting (except after the last one)
            if i < len(analyses) - 1:
                delay = 2 if quick_mode else 5  # Even shorter in quick mode
                print(f"\nWaiting {delay} seconds before next analysis...")
                time.sleep(delay)
            
            elapsed_time = time.time() - start_time
            print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
                
        except Exception as e:
            print(f"Error running analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Add shorter delay before continuing to next analysis
            delay = 5 if quick_mode else 10  # Shorter in quick mode
            print(f"\nError occurred. Waiting {delay} seconds before continuing...")
            time.sleep(delay)

def run_all_analyses_direct(tools_dict, quick_mode=False):
    """Run all available ROI analyses directly without using the agent to minimize API calls."""
    analyses = [
        "calculate_channel_roi",
        "nps_roi_analysis", 
        "stock_index_roi_analysis"
    ]
    
    for i, analysis_func in enumerate(analyses):
        print("\n" + "="*80)
        print(f"\nRunning analysis: {analysis_func}")
        print("="*80 + "\n")
        start_time = time.time()
        
        try:
            print(f"Processing... Please wait...")
            # Direct function call instead of using the agent
            result = tools_dict[analysis_func]()
            print(result)
            
            # Add shorter delay between analyses to avoid rate limiting (except after the last one)
            if i < len(analyses) - 1:
                delay = 2 if quick_mode else 5  # Even shorter in quick mode
                print(f"\nWaiting {delay} seconds before next analysis...")
                time.sleep(delay)
            
            elapsed_time = time.time() - start_time
            print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
                
        except Exception as e:
            print(f"Error running analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Add shorter delay before continuing to next analysis
            delay = 5 if quick_mode else 10  # Shorter in quick mode
            print(f"\nError occurred. Waiting {delay} seconds before continuing...")
            time.sleep(delay)

def extract_monthly_roi_metrics(table_name="Master", total_investment_column="Total Investment", 
                               channels=None, date_column="order_date", gmv_column="gmv", 
                               export_json=False):
    """
    Extract monthly ROI metrics across all marketing channels.
    
    Args:
        table_name: Name of the table containing the data
        total_investment_column: Column name with total investment data
        channels: List of marketing channel columns
        date_column: Column name with date information
        gmv_column: Column name with GMV data
        export_json: Whether to export results as JSON file
        
    Returns:
        DataFrame with monthly ROI metrics
    """
    # Get the data manager and dataframes
    from utils.data_manager import get_data_manager
    data_manager = get_data_manager()
    dataframes = data_manager.get_dataframes()
    
    if table_name not in dataframes:
        return f"Table '{table_name}' not found. Available tables: {', '.join(dataframes.keys())}"
    
    df = dataframes[table_name].copy()
    
    # Define default channels if not provided
    if not channels:
        channels = ["TV", "Radio", "Sponsorship", "Content Marketing", 
                   "Online marketing", "Affiliates", "SEM", "Other"]
    
    # Ensure required columns exist
    required_columns = [date_column, gmv_column, total_investment_column] + channels
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return f"Columns not found: {missing_columns}. Available columns: {', '.join(df.columns)}"
    
    # Convert date column to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])
    
    # Create year-month column for aggregation
    df['year_month'] = df[date_column].dt.to_period('M')
    
    # Convert investment columns from crores to rupees (if needed)
    conversion_factor = 1e7  # 1 crore = 10 million
    investment_columns = [total_investment_column] + [channel for channel in channels if channel != total_investment_column]
    df[investment_columns] = df[investment_columns] * conversion_factor
    
    # Group by month to get monthly GMV and channel investments
    monthly_data = df.groupby('year_month').agg({
        gmv_column: 'sum',
        total_investment_column: 'mean',
        **{channel: 'mean' for channel in channels if channel in df.columns}
    })
    
    # Calculate current month's ROI: Monthly GMV / Monthly Investment
    monthly_data['current_roi'] = monthly_data[gmv_column] / monthly_data[total_investment_column]
    
    # Filter for current month's model (excluding specific months if needed)
    current_months_data = monthly_data.copy()
    
    # Calculate next month's GMV ROI
    current_months_data['next_month_gmv'] = current_months_data[gmv_column].shift(-1)
    current_months_data['next_month_investment'] = current_months_data[total_investment_column].shift(-1)
    current_months_data['next_month_roi'] = current_months_data['next_month_gmv'] / current_months_data['next_month_investment']
    
    # Calculate marginal ROI for all channels
    all_marginal_roi_current = {}
    all_marginal_roi_next = {}
    
    for channel in channels:
        # Current month marginal ROI
        revenue_change = current_months_data[gmv_column].diff()
        investment_change = current_months_data[channel].diff()
        mask = (investment_change != 0) & (investment_change.notna())
        current_months_data[f'{channel}_marginal_roi'] = revenue_change / investment_change
        
        # Next month marginal ROI
        next_revenue_change = current_months_data['next_month_gmv'].diff()
        next_investment_change = current_months_data[channel].shift(-1).diff()
        next_mask = (next_investment_change != 0) & (next_investment_change.notna())
        current_months_data[f'{channel}_next_marginal_roi'] = next_revenue_change / next_investment_change
    
    # Calculate average marginal ROI across all channels for each month
    for idx in current_months_data.index:
        # Current month
        current_marginals = []
        for channel in channels:
            val = current_months_data.loc[idx, f'{channel}_marginal_roi']
            if pd.notna(val) and np.isfinite(val):
                current_marginals.append(val)
        
        # Next month
        next_marginals = []
        for channel in channels:
            val = current_months_data.loc[idx, f'{channel}_next_marginal_roi']
            if pd.notna(val) and np.isfinite(val):
                next_marginals.append(val)
        
        current_months_data.loc[idx, 'avg_marginal_roi'] = np.mean(current_marginals) if current_marginals else np.nan
        current_months_data.loc[idx, 'avg_next_marginal_roi'] = np.mean(next_marginals) if next_marginals else np.nan
    
    # Create a table with the necessary metrics
    results_df = pd.DataFrame({
        'Month': current_months_data.index.astype(str),
        'Current_Monthly_Avg_ROI': current_months_data['current_roi'],
        'Next_Month_ROI': current_months_data['next_month_roi'],
        'Current_Month_Avg_Marginal_ROI': current_months_data['avg_marginal_roi'],
        'Next_Month_Avg_Marginal_ROI': current_months_data['avg_next_marginal_roi']
    })
    
    # Create visualization
    plt.figure(figsize=(14, 10))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    
    # Plot ROI values
    months = results_df['Month']
    ax1.plot(months, results_df['Current_Monthly_Avg_ROI'], 'o-', color='blue', label='Current Monthly Avg ROI')
    ax1.plot(months, results_df['Next_Month_ROI'], 'o-', color='green', label='Next Month ROI')
    ax1.set_ylabel('ROI Value')
    ax1.set_title('Monthly ROI Metrics Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot Marginal ROI values
    ax2.plot(months, results_df['Current_Month_Avg_Marginal_ROI'], 'o-', color='red', label='Current Month Avg Marginal ROI')
    ax2.plot(months, results_df['Next_Month_Avg_Marginal_ROI'], 'o-', color='purple', label='Next Month Avg Marginal ROI')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Marginal ROI Value')
    ax2.set_title('Monthly Marginal ROI Metrics Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save visualization
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = os.path.join(PLOTS_DIR, f"monthly_roi_metrics_{timestamp}.png")
    plt.savefig(plot_path)
    
    print(f"Visualization saved to: {plot_path}")
    
    # Export to JSON if requested
    if export_json:
        # Create a copy for JSON export with proper formatting
        json_export = results_df.copy()
        
        # Format floating point values with 4 decimal places
        for col in json_export.columns:
            if col != 'Month' and json_export[col].dtype == 'float64':
                json_export[col] = json_export[col].map(lambda x: round(x, 4) if pd.notna(x) else None)
        
        # Export to JSON file
        json_path = os.path.join(PLOTS_DIR, f"monthly_roi_metrics_{timestamp}.json")
        json_export.to_json(json_path, orient='records', indent=2)
        print(f"JSON data exported to: {json_path}")
        
        # Also prepare channel-specific data for export
        channel_data = {}
        for channel in channels:
            channel_data[channel] = {
                'current_marginal_roi': current_months_data[[f'{channel}_marginal_roi']].rename(
                    columns={f'{channel}_marginal_roi': 'value'}).to_dict(orient='index'),
                'next_marginal_roi': current_months_data[[f'{channel}_next_marginal_roi']].rename(
                    columns={f'{channel}_next_marginal_roi': 'value'}).to_dict(orient='index')
            }
        
        # Export channel-specific data
        channels_json_path = os.path.join(PLOTS_DIR, f"channel_roi_metrics_{timestamp}.json")
        with open(channels_json_path, 'w') as f:
            import json
            json.dump(channel_data, f, indent=2, default=str)
        print(f"Channel-specific ROI data exported to: {channels_json_path}")
    
    return results_df

if __name__ == "__main__":
    sys.exit(main())