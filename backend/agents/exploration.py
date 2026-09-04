import os
import sys
from typing import List, Dict, Any, Optional
import glob
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import BaseTool, StructuredTool
import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import io
import base64
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("exploration_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("exploration_agent")

def get_data_manager():
    """Get or create the DataManager instance."""
    from utils.data_manager import get_data_manager
    return get_data_manager()

class DataExplorationAgent:
    """
    Agent for exploring and analyzing data with statistical methods.
    This agent works directly with CSV files rather than SQL databases.
    """
    
    def __init__(self, llm: BaseChatModel, data_manager=None):
        """
        Initialize the data exploration agent.
        
        Args:
            llm: Language model to use for the agent
            data_manager: DataManager instance with loaded dataframes
        """
        logger.info("Initializing DataExplorationAgent")
        self.llm = llm
        
        # Use provided data manager or get the default one
        if data_manager is None:
            self.data_manager = get_data_manager()
        else:
            self.data_manager = data_manager
            
        # Get dataframes from the data manager
        self.dataframes = self.data_manager.get_dataframes()
        logger.info(f"DataExplorationAgent using {len(self.dataframes)} dataframes")
        
        # Set up tools
        self.tools = self._create_tools()
        
        # Create the agent executor
        self.agent_executor = self._create_agent()
        logger.info("DataExplorationAgent initialization complete")
    
    def _load_csv_files(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from the data directory."""
        return self.dataframes
    
    def _get_data_schema(self) -> str:
        """Generate schema information about the loaded dataframes."""
        return self.data_manager.get_schema_info()
    
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for data exploration and statistical analysis."""
        logger.info("Creating tools for data exploration")
        
        def get_dataframe(table_name: str) -> Optional[pd.DataFrame]:
            """Get a dataframe by name, with error handling."""
            logger.debug(f"Looking for dataframe: {table_name}")
            if table_name in self.dataframes:
                logger.debug(f"Found dataframe: {table_name}")
                return self.dataframes[table_name]
            else:
                available_tables = ", ".join(self.dataframes.keys())
                error_msg = f"Table '{table_name}' not found. Available tables: {available_tables}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        def list_tables() -> str:
            """List all available tables."""
            logger.info("Tool called: list_tables")
            try:
                tables = list(self.dataframes.keys())
                result = f"Available tables: {', '.join(tables)}"
                logger.info(f"list_tables result: {result}")
                return result
            except Exception as e:
                error_msg = f"Error listing tables: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def preview_data(table_name: str, rows: int = 5) -> str:
            """
            Preview the first few rows of a table.
            
            Args:
                table_name: Name of the table to preview
                rows: Number of rows to show
                
            Returns:
                String with preview data
            """
            logger.info(f"Tool called: preview_data(table_name={table_name}, rows={rows})")
            try:
                df = get_dataframe(table_name)
                with pd.option_context('display.max_rows', rows, 'display.max_columns', 10, 'display.width', 100):
                    preview = df.head(rows).to_string()
                result = f"Preview of {table_name} (first {rows} rows):\n{preview}"
                logger.info(f"preview_data completed for {table_name}")
                return result
            except Exception as e:
                error_msg = f"Error previewing data: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def descriptive_statistics(table_name: str) -> str:
            """
            Generate descriptive statistics for a table.
            
            Args:
                table_name: Name of the table to analyze
                
            Returns:
                String with descriptive statistics
            """
            logger.info(f"Tool called: descriptive_statistics(table_name={table_name})")
            try:
                df = get_dataframe(table_name)
                logger.debug(f"Got dataframe with shape {df.shape}")
                
                # Handle null values
                logger.debug("Handling null values")
                df = df.replace('\\N', np.nan)
                
                # Convert columns to appropriate types where possible
                logger.debug("Converting column types")
                for col in df.columns:
                    try:
                        if df[col].dtype == 'object':
                            # Try to convert to numeric, but keep as string if it fails
                            df[col] = pd.to_numeric(df[col], errors='ignore')
                    except Exception as e:
                        logger.warning(f"Error converting column {col}: {str(e)}")
                
                # Generate statistics with limited output
                logger.debug("Generating descriptive statistics")
                with pd.option_context('display.max_rows', 20, 'display.max_columns', 10, 'display.width', 100):
                    desc_stats = df.describe(include='all').to_string()
                
                # Add additional statistics only for numeric columns that don't have NaN values
                logger.debug("Calculating additional statistics")
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                non_null_cols = [col for col in numeric_cols if not df[col].isnull().any()]
                
                additional_stats = ""
                if len(non_null_cols) > 0:
                    additional_stats += "\n\nAdditional Statistics for Numeric Columns:\n"
                    skew_dict = {}
                    kurt_dict = {}
                    
                    for col in non_null_cols:
                        try:
                            skew_dict[col] = df[col].skew()
                            kurt_dict[col] = df[col].kurt()
                        except Exception as e:
                            logger.warning(f"Error calculating stats for {col}: {str(e)}")
                    
                    additional_stats += f"Skewness: {skew_dict}\n"
                    additional_stats += f"Kurtosis: {kurt_dict}\n"
                
                result = desc_stats + additional_stats
                logger.info(f"descriptive_statistics completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error generating descriptive statistics: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def correlation_analysis(table_name: str, columns: str = None) -> str:
            """
            Perform correlation analysis between columns in a table.
            
            Args:
                table_name: Name of the table to analyze
                columns: Comma-separated list of columns (optional)
                
            Returns:
                String with correlation matrix
            """
            logger.info(f"Tool called: correlation_analysis(table_name={table_name}, columns={columns})")
            try:
                df = get_dataframe(table_name)
                logger.debug(f"Got dataframe with shape {df.shape}")
                
                if columns:
                    logger.debug(f"Filtering columns: {columns}")
                    column_list = [col.strip() for col in columns.split(',')]
                    # Check if all columns exist in the dataframe
                    for col in column_list:
                        if col not in df.columns:
                            logger.warning(f"Column {col} not found in {table_name}")
                            return f"Error: Column '{col}' not found in {table_name}"
                    df = df[column_list]
                
                # Select only numeric columns
                logger.debug("Selecting numeric columns")
                numeric_df = df.select_dtypes(include=[np.number])
                
                if numeric_df.empty:
                    logger.warning("No numeric columns found")
                    return "No numeric columns found for correlation analysis."
                
                logger.debug(f"Calculating correlations for {len(numeric_df.columns)} columns")
                # Calculate correlation matrix
                with pd.option_context('display.max_rows', 20, 'display.max_columns', 10, 'display.width', 100):
                    corr_matrix = numeric_df.corr().round(2).to_string()
                
                result = f"Correlation Matrix:\n{corr_matrix}"
                logger.info(f"correlation_analysis completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error performing correlation analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def time_series_analysis(table_name: str, date_column: str, value_column: str) -> str:
            """
            Analyze time series data.
            
            Args:
                table_name: Name of the table to analyze
                date_column: Column containing dates
                value_column: Column containing values to analyze
                
            Returns:
                String with time series analysis results
            """
            logger.info(f"Tool called: time_series_analysis(table_name={table_name}, date_column={date_column}, value_column={value_column})")
            try:
                df = get_dataframe(table_name)
                logger.debug(f"Got dataframe with shape {df.shape}")
                
                # Check if columns exist
                if date_column not in df.columns:
                    error_msg = f"Date column '{date_column}' not found in {table_name}"
                    logger.error(error_msg)
                    return error_msg
                
                if value_column not in df.columns:
                    error_msg = f"Value column '{value_column}' not found in {table_name}"
                    logger.error(error_msg)
                    return error_msg
                
                # Try to convert date column to datetime
                logger.debug(f"Converting {date_column} to datetime")
                try:
                    df[date_column] = pd.to_datetime(df[date_column])
                except Exception as e:
                    logger.error(f"Error converting {date_column} to datetime: {str(e)}")
                    return f"Error: Unable to convert {date_column} to date format. Please ensure it contains valid dates."
                
                # Sort by date
                logger.debug("Sorting by date")
                df = df.sort_values(by=date_column)
                
                # Basic time series statistics
                logger.debug("Calculating time series statistics")
                min_date = df[date_column].min()
                max_date = df[date_column].max()
                date_range = (max_date - min_date).days
                
                # Calculate period-over-period changes
                logger.debug("Calculating period-over-period changes")
                df['prev_value'] = df[value_column].shift(1)
                df['change'] = df[value_column] - df['prev_value']
                df['pct_change'] = df[value_column].pct_change() * 100
                
                # Calculate overall trend (simple linear regression)
                logger.debug("Calculating trend")
                x = np.arange(len(df))
                y = df[value_column].values
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # Prepare result
                logger.debug("Preparing result")
                result = f"Time Series Analysis for {value_column} over {date_column}:\n\n"
                result += f"Date Range: {min_date} to {max_date} ({date_range} days)\n"
                result += f"Value Range: {df[value_column].min()} to {df[value_column].max()}\n"
                result += f"Mean Value: {df[value_column].mean():.2f}\n"
                result += f"Trend: {slope:.4f} per period (R² = {r_value**2:.4f})\n"
                
                # Add monthly or quarterly aggregation if enough data
                if date_range > 60:
                    logger.debug("Calculating period aggregations")
                    if date_range > 365:
                        # Quarterly aggregation for longer time series
                        df['quarter'] = df[date_column].dt.to_period('Q')
                        quarterly = df.groupby('quarter')[value_column].mean()
                        result += f"\nQuarterly Averages:\n"
                        with pd.option_context('display.max_rows', 10):
                            result += quarterly.to_string()
                    else:
                        # Monthly aggregation for shorter time series
                        df['month'] = df[date_column].dt.to_period('M')
                        monthly = df.groupby('month')[value_column].mean()
                        result += f"\nMonthly Averages:\n"
                        with pd.option_context('display.max_rows', 10):
                            result += monthly.to_string()
                
                logger.info(f"time_series_analysis completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error performing time series analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def segment_analysis(table_name: str, segment_column: str, metric_column: str) -> str:
            """
            Analyze data by segments or categories.
            
            Args:
                table_name: Name of the table to analyze
                segment_column: Column to segment by
                metric_column: Metric to analyze across segments
                
            Returns:
                String with segment analysis results
            """
            logger.info(f"Tool called: segment_analysis(table_name={table_name}, segment_column={segment_column}, metric_column={metric_column})")
            try:
                df = get_dataframe(table_name)
                logger.debug(f"Got dataframe with shape {df.shape}")
                
                # Check if columns exist
                if segment_column not in df.columns:
                    error_msg = f"Segment column '{segment_column}' not found in {table_name}"
                    logger.error(error_msg)
                    return error_msg
                
                if metric_column not in df.columns:
                    error_msg = f"Metric column '{metric_column}' not found in {table_name}"
                    logger.error(error_msg)
                    return error_msg
                
                # Try to convert metric column to numeric if needed
                logger.debug(f"Ensuring {metric_column} is numeric")
                if df[metric_column].dtype == 'object':
                    try:
                        df[metric_column] = pd.to_numeric(df[metric_column], errors='coerce')
                    except Exception as e:
                        logger.error(f"Error converting {metric_column} to numeric: {str(e)}")
                        return f"Error: Unable to convert {metric_column} to numeric for analysis."
                
                # Get basic segment stats
                logger.debug("Calculating segment statistics")
                segment_counts = df[segment_column].value_counts()
                segment_stats = df.groupby(segment_column)[metric_column].agg(['count', 'mean', 'std', 'min', 'max'])
                
                # Calculate relative performance
                logger.debug("Calculating relative performance")
                overall_mean = df[metric_column].mean()
                segment_stats['vs_overall'] = (segment_stats['mean'] / overall_mean - 1) * 100
                
                # Format result
                logger.debug("Formatting result")
                result = f"Segment Analysis for {metric_column} by {segment_column}:\n\n"
                result += f"Overall Statistics for {metric_column}:\n"
                result += f"  Mean: {overall_mean:.2f}\n"
                result += f"  Min: {df[metric_column].min():.2f}\n"
                result += f"  Max: {df[metric_column].max():.2f}\n\n"
                
                result += f"Segment Distribution ({len(segment_counts)} segments):\n"
                with pd.option_context('display.max_rows', 20):
                    result += segment_counts.to_string()
                
                result += f"\n\nSegment Performance:\n"
                with pd.option_context('display.max_rows', 20):
                    result_str = segment_stats.to_string()
                
                result += result_str
                
                logger.info(f"segment_analysis completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error performing segment analysis: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def outlier_detection(table_name: str, column_name: str) -> str:
            """
            Detect outliers in a column using Z-score method.
            
            Args:
                table_name: Name of the table to analyze
                column_name: Column to check for outliers
                
            Returns:
                String with outlier analysis results
            """
            logger.info(f"Tool called: outlier_detection(table_name={table_name}, column_name={column_name})")
            try:
                df = get_dataframe(table_name)
                logger.debug(f"Got dataframe with shape {df.shape}")
                
                # Check if column exists
                if column_name not in df.columns:
                    error_msg = f"Column '{column_name}' not found in {table_name}"
                    logger.error(error_msg)
                    return error_msg
                
                # Try to convert column to numeric if needed
                logger.debug(f"Ensuring {column_name} is numeric")
                if df[column_name].dtype == 'object':
                    try:
                        df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
                    except Exception as e:
                        logger.error(f"Error converting {column_name} to numeric: {str(e)}")
                        return f"Error: Unable to convert {column_name} to numeric for outlier detection."
                
                # Drop NaN values
                logger.debug("Dropping NaN values")
                df = df.dropna(subset=[column_name])
                
                # Calculate Z-scores
                logger.debug("Calculating Z-scores")
                z_scores = np.abs(stats.zscore(df[column_name]))
                
                # Identify outliers (Z-score > 3)
                logger.debug("Identifying outliers")
                outliers = df[z_scores > 3]
                
                outlier_count = len(outliers)
                total_count = len(df)
                outlier_percentage = (outlier_count / total_count) * 100
                
                logger.debug(f"Found {outlier_count} outliers out of {total_count} values")
                output = f"Outlier Analysis for {column_name}:\n"
                output += f"Total values: {total_count}\n"
                output += f"Outliers detected (Z-score > 3): {outlier_count} ({outlier_percentage:.2f}%)\n"
                
                if outlier_count > 0:
                    output += f"\nOutlier Statistics:\n"
                    output += f"Mean of outliers: {outliers[column_name].mean():.2f}\n"
                    output += f"Min outlier: {outliers[column_name].min():.2f}\n"
                    output += f"Max outlier: {outliers[column_name].max():.2f}\n"
                    
                    # Compare with non-outliers
                    non_outliers = df[z_scores <= 3]
                    output += f"\nNon-Outlier Statistics:\n"
                    output += f"Mean of non-outliers: {non_outliers[column_name].mean():.2f}\n"
                    output += f"Standard deviation of non-outliers: {non_outliers[column_name].std():.2f}\n"
                
                logger.info(f"outlier_detection completed for {table_name}")
                return output
                
            except Exception as e:
                error_msg = f"Error detecting outliers: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        # Create tools with better error handling
        logger.info("Creating tool list")
        return [
            StructuredTool.from_function(
                func=list_tables,
                name="list_tables",
                description="List all available data tables"
            ),
            # StructuredTool.from_function(
            #     func=preview_data,
            #     name="preview_data",
            #     description="Preview the first few rows of a table"
            # ),
            StructuredTool.from_function(
                func=descriptive_statistics,
                name="descriptive_statistics",
                description="Generate descriptive statistics for a table (mean, median, std dev, etc.)"
            ),
            StructuredTool.from_function(
                func=correlation_analysis,
                name="correlation_analysis",
                description="Perform correlation analysis between numeric columns in a table. "
            ),
            # StructuredTool.from_function(
            #     func=time_series_analysis,
            #     name="time_series_analysis",
            #     description="Analyze trends over time"
            # ),
        #     StructuredTool.from_function(
        #         func=segment_analysis,
        #         name="segment_analysis",
        #         description="Analyze data by segments or categories to compare metrics. The segment column and metric column should be numeric and not a string. It compares the metric column across the segment column."
        #     ),
        #     StructuredTool.from_function(
        #         func=outlier_detection,
        #         name="outlier_detection",
        #         description="Detect and analyze outliers in a numeric column. The column name provided should be numeric and not a string."
        #     )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the data exploration agent."""
        logger.info("Creating data exploration agent")
        
        # Get data schema information
        data_schema = self._get_data_schema()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a marketing analytics specialist with expertise in advertising effectiveness, 
            campaign performance evaluation, and marketing expenditure analysis. Your goal is to analyze 
            marketing data to extract summary of the uploaded data and statistical analysis about marketing expenditure and its impact.
             
             DO NOT USE THE TOOL WITH THE SAME OBJECTIVE IF IT HAS FAILED OR ALREADY BEEN USED.

            Focus on answering questions such as:
            1. Based on the columns in the table, what is the summary of the data?
            2. Try to focus on columns that are relevant to marketing expenditure and its impact.
            3. Don't make any assumptions, only use the data provided.
            4. Don't perform extra analysis, try to stick to the querie's scope and purpose.
            
            When analyzing marketing expenditure tables:
            - Look for columns like 'channel', 'campaign', 'spend', 'budget', 'impressions', 'clicks', 'ctr'
            - Calculate cost per acquisition (CPA), cost per click (CPC), and return on ad spend (ROAS)
            - Identify high-performing and underperforming channels
            
            When analyzing conversion or revenue data:
            - Connect it back to marketing spend to calculate ROI
            - Look for attribution patterns across channels
            - Analyze conversion rates and customer acquisition costs
            
            When examining customer data:
            - Segment by acquisition channel, customer lifetime value, response rates
            - Analyze which segments respond best to which marketing approaches
            
            Data Schema:
            {data_schema}
            
            Available tools:
            - list_tables: List all available data tables
            - descriptive_statistics: Calculate basic statistics for a table. It can't answer a specific question, it can only provide a summary of the data. Do not use it more than once.
            - correlation_analysis: Find relationships between numeric variables
            
            IMPORTANT: Always check if a tool exists before calling it. Only use tools from the list above.
            Always examine the data before detailed analysis. Start with list_tables, then preview_data, 
            and only then proceed with descriptive_statistics or other analysis.
            
            Example workflow:
            1. First list the tables with list_tables
            2. Preview a table with preview_data
            3. Then analyze with descriptive_statistics
            4. Only use more specific tools after understanding the data structure
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create the agent with tool calling and reduced verbosity
        logger.info("Creating tool calling agent")
        agent = create_tool_calling_agent(
            self.llm,
            self.tools,
            prompt
        )
        
        logger.info("Creating agent executor")
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
    
    def analyze(self, query: str) -> str:
        """
        Analyze data based on the query.
        
        Args:
            query: Analysis question to be answered
            
        Returns:
            str: Analysis results
        """
        logger.info(f"Analyzing query: {query}")
        try:
            result = self.agent_executor.invoke({"input": query})
            logger.info("Analysis completed successfully")
            return result["output"]
        except Exception as e:
            error_msg = f"Error in data exploration: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg

def get_exploration_agent(llm=None, data_manager=None):
    """
    Create a data exploration agent.
    
    Args:
        llm: Language model to use (defaults to ChatGroq if None)
        data_manager: DataManager instance with loaded dataframes
        
    Returns:
        DataExplorationAgent instance
    """
    logger.info("Creating exploration agent")
    if llm is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=api_key)
    return DataExplorationAgent(llm, data_manager)

def main():
    """Run a sample data exploration."""
    logger.info("Starting main exploration function")
    agent = get_exploration_agent()
    
    # Sample queries
    queries = [
        "What is the correlation between the units sold and the gmv?"
    ]
    
    for query in queries:
        logger.info(f"Running query: {query}")
        print(f"\n\nQuery: {query}")
        print("-" * 50)
        result = agent.analyze(query)
        print(result)
        print("=" * 50)
    
    logger.info("Sample exploration completed")

if __name__ == "__main__":
    main() 