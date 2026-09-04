import os
import sys
from typing import List, Dict, Any, Optional
import logging
import glob
import time
import datetime
import gc

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

# Import the data manager
from utils.data_manager import get_data_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kpi_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("kpi_agent")

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)
    logger.info(f"Created plots directory at {PLOTS_DIR}")
else:
    logger.info(f"Using existing plots directory at {PLOTS_DIR}")

class KPIAgent:
    """
    Agent for analyzing KPIs and performance drivers in marketing data.
    """
    
    def __init__(self, llm: BaseChatModel, data_manager=None):
        """
        Initialize the KPI analysis agent.
        
        Args:
            llm: Language model to use for the agent
            data_manager: DataManager instance with loaded dataframes
        """
        logger.info("Initializing KPIAgent")
        self.llm = llm
        
        # Use provided data manager or get the default one
        if data_manager is None:
            self.data_manager = get_data_manager()
        else:
            self.data_manager = data_manager
            
        # Get dataframes from the data manager
        self.dataframes = self.data_manager.get_dataframes()
        
        logger.info(f"KPIAgent using {len(self.dataframes)} dataframes")
        
        # Set up tools
        self.tools = self._create_tools()
        
        # Create the agent executor
        self.agent_executor = self._create_agent()
        logger.info("KPIAgent initialization complete")
    
    def _get_data_schema(self) -> str:
        """Generate schema information about the loaded dataframes."""
        return self.data_manager.get_schema_info()

    def _create_tools(self) -> List[BaseTool]:
        """Create tools for KPI analysis."""
        logger.info("Creating tools for KPI analysis")
        
        def monthly_gmv_sla_analysis(table_name: str = 'Master') -> str:
            """
            Analyze the relationship between individual GMV and SLA values.
            
            Args:
                table_name: Name of the table containing the data
                
            Returns:
                String with analysis results
            """
            logger.info(f"Tool called: monthly_gmv_sla_analysis")
            try:
                # Only select the columns we need instead of copying the entire dataframe
                cols_needed = ['gmv', 'sla']
                df = self.dataframes[table_name]
                
                # Check if dataframe is empty
                if df.empty:
                    return "Error: No data available for analysis."
                df = df[cols_needed]
                
                # Calculate correlation between individual GMV and SLA values
                correlation = df['gmv'].corr(df['sla'])
                
                # Generate result
                result = "GMV vs SLA Analysis (Individual Orders):\n\n"
                result += f"Correlation between GMV and SLA: {correlation:.4f}\n\n"
                
                # Create visualization
                plt.figure(figsize=(12, 6))
                
                # Create scatter plot with density coloring due to large number of points
                plt.hist2d(df['sla'], df['gmv'], bins=50, cmap='viridis', norm=plt.matplotlib.colors.LogNorm())
                plt.colorbar(label='Count of Orders')
                
                plt.xlabel('SLA (days)')
                plt.ylabel('GMV')
                plt.title('GMV vs SLA (Individual Orders)')
                
                # Add trend line
                z = np.polyfit(df['sla'], df['gmv'], 1)
                p = np.poly1d(z)
                plt.plot(df['sla'], p(df['sla']), "r--", alpha=0.8, label='Trend Line')
                plt.legend()
                
                plt.tight_layout()
                
                # Save figure to buffer for base64 encoding
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                
                # Save figure to file
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_filename = f"gmv_sla_analysis_{timestamp}.png"
                plot_path = os.path.join(PLOTS_DIR, plot_filename)
                plt.savefig(plot_path)
                plt.close()
                
                logger.info(f"Saved GMV vs SLA plot to {plot_path}")
                
                # Convert to base64
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                
                # Add insights
                result += f"Plot saved to: {plot_path}\n\n"
                result += "Key Insights:\n"
                result += f"1. Average SLA: {df['sla'].mean():.2f} days\n"
                result += f"2. Average GMV: ${df['gmv'].mean():,.2f}\n"
                result += f"3. SLA Range: {df['sla'].min():.1f} to {df['sla'].max():.1f} days\n"
                result += f"4. GMV Range: ${df['gmv'].min():,.2f} to ${df['gmv'].max():,.2f}\n"
                
                # Add correlation interpretation
                if correlation > 0:
                    result += "5. There is a positive correlation between SLA and GMV, suggesting that orders with higher GMV tend to have longer SLA\n"
                else:
                    result += "5. There is a negative correlation between SLA and GMV, suggesting that orders with higher GMV tend to have shorter SLA\n"
                
                # Add SLA distribution insights
                percentiles = df['sla'].quantile([0.25, 0.5, 0.75])
                result += "\nSLA Distribution:\n"
                result += f"- 25% of orders have SLA <= {percentiles[0.25]:.1f} days\n"
                result += f"- 50% of orders have SLA <= {percentiles[0.5]:.1f} days\n"
                result += f"- 75% of orders have SLA <= {percentiles[0.75]:.1f} days\n"
                
                # Force cleanup of dataframe
                del df
                gc.collect()

                logger.info(result)
                
                return result
                
            except Exception as e:
                error_msg = f"Error in GMV vs SLA analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg

        def monthly_gmv_nps_analysis(table_name: str = 'Master') -> str:
            """
            Analyze the relationship between current month's NPS score and next month's GMV.
            This analysis shows how customer satisfaction impacts future sales.
            
            Args:
                table_name: Name of the table containing the data
                
            Returns:
                String with analysis results
            """
            logger.info(f"Tool called: monthly_gmv_nps_analysis")
            try:
                # Only select the columns we need
                cols_needed = ['gmv', 'NPS_Score', 'order_date']
                df = self.dataframes[table_name]
                
                df = df[cols_needed]
                
                # Check if dataframe is empty
                if df.empty:
                    return "Error: No data available for analysis."
                
                # Remove NaN values
                df = df.dropna(subset=['gmv', 'NPS_Score', 'order_date'])
                
                # Check if we still have data after removing NaN values
                if len(df) == 0:
                    return "Error: No valid data available after removing missing values."
                
                # Convert order_date to datetime if not already
                df['order_date'] = pd.to_datetime(df['order_date'])
                
                # Create year_month column for grouping
                df['year_month'] = df['order_date'].dt.to_period('M')
                
                # Check if we have enough months for analysis
                if df['year_month'].nunique() < 2:
                    return "Error: Need at least two months of data for this analysis."
                
                # Group by month and calculate monthly GMV and average NPS
                monthly_metrics = df.groupby('year_month').agg({
                    'gmv': 'sum',
                    'NPS_Score': 'mean'
                }).reset_index()
                
                # Once we've aggregated, we can release the main dataframe
                del df
                gc.collect()
                
                # Sort by year_month to ensure chronological order
                monthly_metrics = monthly_metrics.sort_values('year_month')
                
                # Create shifted GMV column (next month's GMV)
                monthly_metrics['next_month_gmv'] = monthly_metrics['gmv'].shift(-1)
                
                # Drop the last row as it won't have a next month's GMV
                monthly_metrics = monthly_metrics.dropna(subset=['next_month_gmv'])
                
                # Check if we have enough data points after shifting
                if len(monthly_metrics) < 2:
                    return "Error: Not enough monthly data points for correlation analysis after shifting."
                
                # Convert year_month to string for plotting
                monthly_metrics['year_month_str'] = monthly_metrics['year_month'].astype(str)
                
                # Calculate correlation between current month's NPS and next month's GMV
                correlation = monthly_metrics['NPS_Score'].corr(monthly_metrics['next_month_gmv'])
                
                # Generate result
                result = "Current Month NPS vs Next Month GMV Analysis:\n\n"
                result += f"Correlation between Current Month NPS and Next Month GMV: {correlation:.4f}\n\n"
                
                plot_path = ""
                try:
                    # Create visualization
                    plt.figure(figsize=(12, 6))
                    
                    # Create scatter plot
                    plt.scatter(monthly_metrics['NPS_Score'], monthly_metrics['next_month_gmv'])
                    
                    # Add data point labels (month names)
                    for i, row in monthly_metrics.iterrows():
                        plt.annotate(row['year_month_str'], 
                                    (row['NPS_Score'], row['next_month_gmv']),
                                    textcoords="offset points", 
                                    xytext=(0,10), 
                                    ha='center')
                    
                    plt.xlabel('Current Month Average NPS Score')
                    plt.ylabel('Next Month GMV')
                    plt.title('Impact of Current Month NPS on Next Month GMV')
                    
                    # Add trend line
                    if len(monthly_metrics) > 1:  # Need at least 2 points for a trend line
                        z = np.polyfit(monthly_metrics['NPS_Score'], monthly_metrics['next_month_gmv'], 1)
                        p = np.poly1d(z)
                        plt.plot(monthly_metrics['NPS_Score'], p(monthly_metrics['NPS_Score']), "r--", alpha=0.8, label='Trend Line')
                        plt.legend()
                    
                    plt.tight_layout()
                    
                    # Save figure to buffer for base64 encoding
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    
                    # Save figure to file
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    plot_filename = f"nps_next_month_gmv_{timestamp}.png"
                    plot_path = os.path.join(PLOTS_DIR, plot_filename)
                    plt.savefig(plot_path)
                    plt.close()
                    
                    logger.info(f"Saved NPS vs Next Month GMV plot to {plot_path}")
                    
                    # Convert to base64
                    img_str = base64.b64encode(buffer.read()).decode('utf-8')
                    
                    result += f"Plot saved to: {plot_path}\n\n"
                except Exception as viz_error:
                    logger.error(f"Error creating visualization: {str(viz_error)}")
                    logger.error(traceback.format_exc())
                    result += "Note: Could not generate visualization due to an error.\n\n"
                
                # Add insights
                result += "Key Insights:\n"
                result += f"1. Average Monthly NPS Score: {monthly_metrics['NPS_Score'].mean():.2f}\n"
                result += f"2. Average Next Month GMV: ${monthly_metrics['next_month_gmv'].mean():,.2f}\n"
                
                # Add correlation interpretation
                if correlation > 0.7:
                    result += "3. There is a strong positive correlation between current month NPS and next month GMV, suggesting that higher customer satisfaction leads to significantly increased future sales\n"
                elif correlation > 0.3:
                    result += "3. There is a moderate positive correlation between current month NPS and next month GMV, suggesting that higher customer satisfaction contributes to increased future sales\n"
                elif correlation > 0:
                    result += "3. There is a weak positive correlation between current month NPS and next month GMV, suggesting that customer satisfaction may have a small positive impact on future sales\n"
                elif correlation > -0.3:
                    result += "3. There is a weak negative correlation between current month NPS and next month GMV, suggesting that customer satisfaction may not be driving future sales as expected\n"
                else:
                    result += "3. There is a moderate to strong negative correlation between current month NPS and next month GMV, which is counterintuitive and warrants further investigation\n"
                
                # Add month-to-month analysis
                if len(monthly_metrics) > 2:
                    try:
                        # Find months with highest and lowest NPS
                        highest_nps_month = monthly_metrics.loc[monthly_metrics['NPS_Score'].idxmax()]
                        lowest_nps_month = monthly_metrics.loc[monthly_metrics['NPS_Score'].idxmin()]
                        
                        result += f"\n4. The month with highest NPS ({highest_nps_month['year_month_str']}, NPS: {highest_nps_month['NPS_Score']:.2f}) "
                        result += f"was followed by a next month GMV of ${highest_nps_month['next_month_gmv']:,.2f}\n"
                        
                        result += f"5. The month with lowest NPS ({lowest_nps_month['year_month_str']}, NPS: {lowest_nps_month['NPS_Score']:.2f}) "
                        result += f"was followed by a next month GMV of ${lowest_nps_month['next_month_gmv']:,.2f}\n"
                    except Exception as month_error:
                        logger.error(f"Error in month-to-month analysis: {str(month_error)}")
                        # Continue with the rest of the analysis
            
                
                # Force cleanup
                del monthly_metrics
                gc.collect()

                logger.info(result)
                
                return result
                
            except Exception as e:
                error_msg = f"Error in monthly GMV vs NPS analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg

        def gmv_discount_analysis(table_name: str = 'Master') -> str:
            """
            Analyze the relationship between GMV and discount across all orders.
            
            Args:
                table_name: Name of the table containing the data
                
            Returns:
                String with analysis results
            """
            logger.info(f"Tool called: gmv_discount_analysis")
            try:
                # Only select the columns we need to conserve memory
                cols_needed = ['gmv', 'units', 'product_mrp']
                df = self.dataframes[table_name]
                
                # Check if dataframe is empty before copying
                if df.empty:
                    return "Error: No data available for analysis."
                
                # Create a view with only required columns
                df = df[cols_needed]
                # Remove NaN values before calculation
                df = df.dropna(subset=['gmv', 'units', 'product_mrp'])
                
                # Calculate discount percentage using the correct formula: (mrp - gmv/units)/mrp * 100
                df['discount_percentage'] = ((df['product_mrp'] - (df['gmv']/df['units'])) / df['product_mrp']) * 100
                
                # Remove unnecessary columns to free memory
                df = df[['gmv', 'discount_percentage']]
                
                # Remove infinite and NaN values
                df = df[np.isfinite(df['discount_percentage'])]
                df = df[np.isfinite(df['gmv'])]
                
                # Remove outliers (optional)
                df = df[df['discount_percentage'] <= 100]  # Remove discounts > 100%
                df = df[df['discount_percentage'] >= 0]    # Remove negative discounts
                
                # Calculate correlation
                correlation = df['gmv'].corr(df['discount_percentage'])
                
                # Generate result
                result = "GMV vs Discount Analysis:\n\n"
                result += f"Correlation between GMV and Discount Percentage: {correlation:.4f}\n\n"
                
                # Create visualization
                plt.figure(figsize=(12, 6))
                
                # Create scatter plot instead of hist2d to avoid NaN issues
                plt.scatter(df['discount_percentage'], df['gmv'], alpha=0.5, s=5)
                
                plt.xlabel('Discount Percentage')
                plt.ylabel('GMV')
                plt.title('GMV vs Discount Percentage')
                
                # Add trend line
                z = np.polyfit(df['discount_percentage'], df['gmv'], 1)
                p = np.poly1d(z)
                plt.plot(df['discount_percentage'], p(df['discount_percentage']), "r--", alpha=0.8)
                
                plt.tight_layout()
                
                # Save figure to buffer for base64 encoding
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                
                # Save figure to file
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_filename = f"gmv_discount_{timestamp}.png"
                plot_path = os.path.join(PLOTS_DIR, plot_filename)
                plt.savefig(plot_path)
                plt.close()
                
                logger.info(f"Saved GMV vs Discount plot to {plot_path}")
                
                # Convert to base64
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                
                # Close buffer
                buffer.close()
                
                # Free plot dataframe memory if it was a sample
                if 'plot_df' in locals() and id(plot_df) != id(df):
                    del plot_df
                
                # Add insights
                result += f"Plot saved to: {plot_path}\n\n"
                result += "Key Insights:\n"
                result += f"1. Average Discount Percentage: {df['discount_percentage'].mean():.2f}%\n"
                result += f"2. Average GMV: ${df['gmv'].mean():,.2f}\n"
                result += f"3. Most Common Discount Range: {df['discount_percentage'].quantile(0.5):.1f}%\n"
                if correlation > 0:
                    result += "4. Higher discounts tend to lead to higher GMV\n"
                else:
                    result += "4. Higher discounts tend to lead to lower GMV\n"
                
                # Force cleanup
                del df
                gc.collect()
                logger.info(result)
                return result
                
            except Exception as e:
                error_msg = f"Error in GMV vs discount analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg

        # Create tools list
        return [
            StructuredTool.from_function(
                func=monthly_gmv_sla_analysis,
                name="monthly_gmv_sla_analysis",
                description="Analyze the relationship between individual GMV and SLA values"
            ),
            StructuredTool.from_function(
                func=monthly_gmv_nps_analysis,
                name="monthly_gmv_nps_analysis",
                description="Analyze the relationship between current month's NPS score and next month's GMV"
            ),
            StructuredTool.from_function(
                func=gmv_discount_analysis,
                name="gmv_discount_analysis",
                description="Analyze the relationship between GMV and discount across all orders"
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the KPI analysis agent."""
        logger.info("Creating KPI analysis agent")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a marketing KPI data generator. Your task is to extract KPI analysis data using the tools provided.
            
            Here is the schema of the available data:
            {self._get_data_schema()}
            
            You have access to marketing performance data and can use the following tools:
            - monthly_gmv_sla_analysis: Analyze the relationship between individual GMV and SLA values
            - monthly_gmv_nps_analysis: Analyze the relationship between current month's NPS score and next month's GMV
            - gmv_discount_analysis: Analyze the relationship between GMV and discount across all orders
            
            
            IMPORTANT: In your final response, be sure to include the values of:

            1. The month with highest NPS along with value
                was followed by a next month GMV of highest_nps_month['next_month_gmv']
            2. The month with lowest NPS along with value
                was followed by a next month GMV of lowest_nps_month['next_month_gmv']
            3. Average Discount Percentage
            4. Average GMV
            5. Most Common Discount Range
            6. Correlation between Current Month NPS and Next Month GMV
            7. Correlation between GMV and Discount Percentage
            .... ETC
                
            NOTE:     

            1. Complete numerical data from all analyses you run (correlations, averages, ranges, etc.)
            2. Detailed findings about relationships between metrics (e.g., NPS impact on GMV, discount impact on sales)
            3. All key statistical insights (include exact numbers with proper formatting)
            4. References to the visualizations that were generated and their key insights
            
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
        Analyze KPIs based on the query.
        
        Args:
            query: Analysis question to be answered
            
        Returns:
            str: Analysis results
        """
        logger.info(f"Analyzing KPI query: {query}")
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                result = self.agent_executor.invoke({"input": query})
                logger.info(result)
                logger.info("KPI analysis completed successfully")
                return result["output"]
            except Exception as e:
                attempt += 1
                error_msg = f"Error in KPI analysis (attempt {attempt}/{max_attempts}): {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
                if attempt < max_attempts:
                    # Wait longer between each retry
                    wait_time = 20 * attempt
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Error in KPI analysis after {max_attempts} attempts: {str(e)}"

def get_kpi_agent(llm=None, data_manager=None):
    """Create a KPI analysis agent."""
    logger.info("Creating KPI agent")
    if llm is None:
        try:
            # Try to get API key from environment variable first
            import os
            api_key = os.environ.get("GROQ_API_KEY")
            
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            llm = ChatGroq(
                api_key=api_key,
                model="llama-3.3-70b-versatile",  # Using a smaller model for faster responses
                temperature=0,                 # Deterministic outputs
                max_retries=5,                 # Increased retries
                timeout=90                     # Longer timeout
            )
            logger.info("Successfully initialized Groq LLM")
        except Exception as e:
            logger.error(f"Error initializing Groq LLM: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to initialize language model: {str(e)}")
    
    try:
        # Create or get the data manager with the specified data directory
        data_manager = data_manager if data_manager else get_data_manager()
        
        # Create the KPI agent with the shared data manager
        agent = KPIAgent(llm, data_manager)
        return agent
    except Exception as e:
        logger.error(f"Error creating KPI agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to create KPI agent: {str(e)}")

def run_all_analyses(agent):
    """Run all available KPI analyses and print results."""
    analyses = [
        "Analyze the relationship between GMV and SLA for all orders",
        "Analyze the relationship between current month's NPS score and next month's GMV",
        "Analyze the relationship between GMV and discount percentages"
    ]
    
    for i, analysis in enumerate(analyses):
        print("\n" + "="*80)
        print(f"\nRunning analysis: {analysis}")
        print("="*80 + "\n")
        try:
            result = agent.invoke(analysis)
            print(result)
            
            # Add delay between analyses to avoid rate limiting (except after the last one)
            if i < len(analyses) - 1:
                delay = 30  # 30 seconds delay between analyses
                print(f"\nWaiting {delay} seconds before next analysis to avoid rate limiting...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error running analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Add delay before continuing to next analysis
            delay = 45  # Longer delay after an error
            print(f"\nError occurred. Waiting {delay} seconds before continuing...")
            time.sleep(delay)

def main():
    """Main function to run the KPI analysis."""
    print("\nInitializing KPI Analysis Agent...")
    print("="*80)
    
    try:
        # Initialize the agent
        agent = get_kpi_agent()
        
        # Print information about plots directory
        print(f"\nPlots will be saved to: {PLOTS_DIR}")
        print("You can view the generated plots in this directory after each analysis.")
        
        while True:
            print("\nKPI Analysis Options:")
            print("1. Analyze GMV vs SLA (all orders)")
            print("2. Analyze Current Month NPS vs Next Month GMV")
            print("3. Analyze GMV vs Discount")
            print("4. Run All Analyses")
            print("5. Custom Analysis Query")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ")
            
            try:
                if choice == '1':
                    result = agent.invoke("Analyze the relationship between GMV and SLA for all orders")
                    print("\nResults:")
                    print(result)
                
                elif choice == '2':
                    result = agent.invoke("Analyze the relationship between current month's NPS score and next month's GMV")
                    print("\nResults:")
                    print(result)
                
                elif choice == '3':
                    result = agent.invoke("Analyze the relationship between GMV and discount percentages")
                    print("\nResults:")
                    print(result)
                
                elif choice == '4':
                    run_all_analyses(agent)
                
                elif choice == '5':
                    query = input("\nEnter your analysis query: ")
                    result = agent.invoke(query)
                    print("\nResults:")
                    print(result)
                
                elif choice == '6':
                    print("\nExiting KPI Analysis Tool...")
                    break
                
                else:
                    print("\nInvalid choice. Please try again.")
            
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

if __name__ == "__main__":
    sys.exit(main()) 