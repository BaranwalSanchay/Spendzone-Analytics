import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import glob
import logging
import time
import functools
import groq
from groq import APIStatusError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import BaseTool, StructuredTool
import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import traceback
from dotenv import load_dotenv

# Import the data manager
from utils.data_manager import get_data_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("budget_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("budget_agent")

# Create plots directory if it doesn't exist
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)
    logger.info(f"Created plots directory at {PLOTS_DIR}")
else:
    logger.info(f"Using existing plots directory at {PLOTS_DIR}")

class BudgetAgent:
    """
    Agent for optimizing marketing budget allocation and forecasting returns.
    """
    
    def __init__(self, llm: BaseChatModel, data_manager=None):
        """
        Initialize the budget allocation agent.
        
        Args:
            llm: Language model to use for the agent
            data_manager: DataManager instance with loaded dataframes
        """
        logger.info("Initializing BudgetAgent")
        self.llm = llm
        
        # Use provided data manager or get the default one
        if data_manager is None:
            self.data_manager = get_data_manager()
        else:
            self.data_manager = data_manager
            
        # Get dataframes from the data manager
        self.dataframes = self.data_manager.get_dataframes()
        
        logger.info(f"BudgetAgent using {len(self.dataframes)} dataframes")
        
        # Set up tools
        self.tools = self._create_tools()
        
        # Create the agent executor
        self.agent_executor = self._create_agent()
        logger.info("BudgetAgent initialization complete")
    
    def _get_data_schema(self) -> str:
        """Generate schema information about the loaded dataframes."""
        return self.data_manager.get_schema_info()
    
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for budget optimization."""
        logger.info("Creating tools for budget optimization")
        
        def optimize_budget_allocation(table_name: str, channel_column: str, spend_column: str, revenue_column: str) -> str:
            """
            Optimize marketing budget allocation across channels based on ROI analysis.
            
            Args:
                table_name: Name of the table containing channel performance data
                channel_column: Column name with channel information
                spend_column: Column name with marketing spend data
                revenue_column: Column name with revenue data
                
            Returns:
                String with optimized budget allocation recommendations
            """
            logger.info(f"Tool called: optimize_budget_allocation")
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name].copy()
                
                # Ensure columns exist
                for col in [channel_column, spend_column, revenue_column]:
                    if col not in df.columns:
                        return f"Column '{col}' not found in table. Available columns: {', '.join(df.columns)}"
                
                # Aggregate data by channel
                channel_data = df.groupby(channel_column).agg({
                    spend_column: 'sum',
                    revenue_column: 'sum'
                }).reset_index()
                
                # Calculate ROI and ROAS
                channel_data['roi'] = (channel_data[revenue_column] - channel_data[spend_column]) / channel_data[spend_column]
                channel_data['roas'] = channel_data[revenue_column] / channel_data[spend_column]
                
                # Get current total budget
                total_budget = channel_data[spend_column].sum()
                
                # Model elasticity for each channel (simplified approach)
                elasticities = {}
                for i, row in channel_data.iterrows():
                    channel = row[channel_column]
                    roas = row['roas']
                    
                    # Simple elasticity model based on ROAS
                    # Higher ROAS channels get higher elasticity (responsiveness to spend)
                    elasticity = min(0.8, max(0.2, 0.3 + 0.05 * min(roas, 10)))
                    elasticities[channel] = elasticity
                
                # Optimization function
                # This calculates expected revenue based on budget allocation and elasticities
                def neg_expected_revenue(allocations):
                    allocated = dict(zip(channel_data[channel_column], allocations))
                    expected_revenue = 0
                    
                    for i, row in channel_data.iterrows():
                        channel = row[channel_column]
                        current_spend = row[spend_column]
                        current_revenue = row[revenue_column]
                        elasticity = elasticities[channel]
                        
                        # Revenue model: R = current_revenue * (new_spend/current_spend)^elasticity
                        if current_spend > 0:
                            channel_revenue = current_revenue * (allocated[channel]/current_spend)**elasticity
                        else:
                            # For channels with no current spend, use average ROAS
                            channel_revenue = allocated[channel] * channel_data['roas'].mean()
                            
                        expected_revenue += channel_revenue
                    
                    # Return negative because we want to maximize, but scipy minimizes
                    return -expected_revenue
                
                # Constraints
                # 1. Total budget must equal current total budget
                # 2. Each channel must have non-negative spend
                constraints = [
                    {'type': 'eq', 'fun': lambda x: sum(x) - total_budget}
                ]
                
                bounds = [(0, None) for _ in range(len(channel_data))]
                
                # Initial guess - equal distribution
                initial_guess = [total_budget / len(channel_data) for _ in range(len(channel_data))]
                
                # Run optimization
                result = minimize(
                    neg_expected_revenue,
                    initial_guess,
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints
                )
                
                # Get optimized allocations
                optimized_allocations = dict(zip(channel_data[channel_column], result.x))
                
                # Add optimized allocation to channel data
                channel_data['optimal_spend'] = channel_data[channel_column].map(optimized_allocations)
                channel_data['spend_change'] = channel_data['optimal_spend'] - channel_data[spend_column]
                channel_data['spend_change_pct'] = (channel_data['spend_change'] / channel_data[spend_column]) * 100
                
                # Sort by optimal spend
                channel_data = channel_data.sort_values('optimal_spend', ascending=False)
                
                # Calculate expected revenue
                expected_revenue = -neg_expected_revenue(result.x)
                current_revenue = channel_data[revenue_column].sum()
                revenue_increase = expected_revenue - current_revenue
                revenue_increase_pct = (revenue_increase / current_revenue) * 100
                
                # Format results
                result_str = "# Optimal Budget Allocation Recommendation\n\n"
                result_str += f"## Summary\n"
                result_str += f"Total marketing budget: ${total_budget:,.2f}\n"
                result_str += f"Expected revenue with optimal allocation: ${expected_revenue:,.2f}\n"
                result_str += f"Projected revenue increase: ${revenue_increase:,.2f} ({revenue_increase_pct:.2f}%)\n\n"
                
                result_str += "## Channel-Specific Recommendations\n\n"
                
                for i, row in channel_data.iterrows():
                    result_str += f"### {row[channel_column]}\n"
                    result_str += f"- Current spend: ${row[spend_column]:,.2f} ({(row[spend_column]/total_budget)*100:.1f}% of budget)\n"
                    result_str += f"- Recommended spend: ${row['optimal_spend']:,.2f} ({(row['optimal_spend']/total_budget)*100:.1f}% of budget)\n"
                    result_str += f"- Change: ${row['spend_change']:,.2f} ({row['spend_change_pct']:.1f}%)\n"
                    result_str += f"- Current ROAS: {row['roas']:.2f}\n"
                    result_str += f"- Current ROI: {row['roi']:.2f} ({row['roi']*100:.1f}%)\n\n"
                
                # Create pie charts to compare current vs. optimal allocation
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
                
                # Current allocation
                ax1.pie(
                    channel_data[spend_column],
                    labels=channel_data[channel_column],
                    autopct='%1.1f%%',
                    startangle=90,
                    shadow=False
                )
                ax1.set_title('Current Budget Allocation')
                
                # Optimal allocation
                ax2.pie(
                    channel_data['optimal_spend'],
                    labels=channel_data[channel_column],
                    autopct='%1.1f%%',
                    startangle=90,
                    shadow=False
                )
                ax2.set_title('Recommended Budget Allocation')
                
                plt.tight_layout()
                
                # Save figure to buffer
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                plt.close()
                
                # Convert to base64 for embedding in markdown
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                
                # Create bar chart of spend changes
                plt.figure(figsize=(12, 6))
                
                # Sort by spend change percentage for the chart
                chart_data = channel_data.sort_values('spend_change_pct', ascending=False)
                
                # Create colormap based on positive/negative change
                colors = ['green' if x > 0 else 'red' for x in chart_data['spend_change_pct']]
                
                plt.bar(
                    chart_data[channel_column],
                    chart_data['spend_change_pct'],
                    color=colors
                )
                plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
                plt.title('Recommended Budget Reallocation by Channel')
                plt.ylabel('Change in Budget (%)')
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add values on top of bars
                for i, val in enumerate(chart_data['spend_change_pct']):
                    plt.text(
                        i, 
                        val + (5 if val > 0 else -10), 
                        f"{val:.1f}%",
                        ha='center',
                        va='center',
                        fontweight='bold'
                    )
                
                plt.tight_layout()
                
                # Save figure to buffer
                buffer2 = io.BytesIO()
                plt.savefig(buffer2, format='png')
                buffer2.seek(0)
                plt.close()
                
                # Convert to base64
                img_str2 = base64.b64encode(buffer2.read()).decode('utf-8')
                
                # Add images to result
                result_str += f"## Visualization of Budget Allocation\n\n"
                result_str += f"![Budget Allocation Comparison](data:image/png;base64,{img_str})\n\n"
                result_str += f"## Recommended Changes by Channel\n\n"
                result_str += f"![Budget Change by Channel](data:image/png;base64,{img_str2})\n\n"
                
                # Implementation guidelines
                result_str += "## Implementation Guidelines\n\n"
                result_str += "1. **Gradual Transition**: Implement budget changes gradually over 2-3 months to monitor impact\n"
                result_str += "2. **Testing Approach**: A/B test new allocations against control groups where possible\n"
                result_str += "3. **Performance Monitoring**: Establish weekly performance reviews of channels receiving major increases\n"
                result_str += "4. **Risk Management**: For channels receiving significant budget decreases, maintain minimum presence to avoid losing market position\n"
                result_str += "5. **Seasonal Adjustments**: Adjust these recommendations during seasonal peaks or promotional periods\n"
                
                logger.info(f"Budget optimization completed for {table_name}")
                return result_str
                
            except Exception as e:
                error_msg = f"Error in budget optimization: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def prioritize_product_categories(table_name: str, category_column: str, revenue_column: str, 
                                          margin_column: str = None, growth_column: str = None) -> str:
            """
            Identify product categories that should be prioritized in marketing campaigns.
            
            Args:
                table_name: Name of the table containing product category data
                category_column: Column name with product category information
                revenue_column: Column name with revenue data
                margin_column: Column name with margin data (optional)
                growth_column: Column name with growth data (optional)
                
            Returns:
                String with category prioritization recommendations
            """
            logger.info(f"Tool called: prioritize_product_categories")
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name].copy()
                
                # Ensure columns exist
                if category_column not in df.columns:
                    return f"Column '{category_column}' not found in table. Available columns: {', '.join(df.columns)}"
                
                if revenue_column not in df.columns:
                    return f"Column '{revenue_column}' not found in table. Available columns: {', '.join(df.columns)}"
                
                # Aggregate data by category
                category_data = df.groupby(category_column).agg({
                    revenue_column: 'sum'
                }).reset_index()
                
                # Add margin and growth if available
                if margin_column and margin_column in df.columns:
                    category_margin = df.groupby(category_column)[margin_column].mean().reset_index()
                    category_data = pd.merge(category_data, category_margin, on=category_column)
                
                if growth_column and growth_column in df.columns:
                    category_growth = df.groupby(category_column)[growth_column].mean().reset_index()
                    category_data = pd.merge(category_data, category_growth, on=category_column)
                
                # Calculate priority score
                # Default weights if both margin and growth are available
                if margin_column and margin_column in df.columns and growth_column and growth_column in df.columns:
                    # Normalize values to 0-1 range
                    revenue_norm = (category_data[revenue_column] - category_data[revenue_column].min()) / (category_data[revenue_column].max() - category_data[revenue_column].min())
                    margin_norm = (category_data[margin_column] - category_data[margin_column].min()) / (category_data[margin_column].max() - category_data[margin_column].min())
                    growth_norm = (category_data[growth_column] - category_data[growth_column].min()) / (category_data[growth_column].max() - category_data[growth_column].min())
                    
                    # Calculate priority score (weighted average)
                    category_data['priority_score'] = (revenue_norm * 0.4) + (margin_norm * 0.3) + (growth_norm * 0.3)
                
                # If only margin is available
                elif margin_column and margin_column in df.columns:
                    revenue_norm = (category_data[revenue_column] - category_data[revenue_column].min()) / (category_data[revenue_column].max() - category_data[revenue_column].min())
                    margin_norm = (category_data[margin_column] - category_data[margin_column].min()) / (category_data[margin_column].max() - category_data[margin_column].min())
                    
                    category_data['priority_score'] = (revenue_norm * 0.6) + (margin_norm * 0.4)
                
                # If only growth is available
                elif growth_column and growth_column in df.columns:
                    revenue_norm = (category_data[revenue_column] - category_data[revenue_column].min()) / (category_data[revenue_column].max() - category_data[revenue_column].min())
                    growth_norm = (category_data[growth_column] - category_data[growth_column].min()) / (category_data[growth_column].max() - category_data[growth_column].min())
                    
                    category_data['priority_score'] = (revenue_norm * 0.6) + (growth_norm * 0.4)
                
                # If only revenue is available
                else:
                    revenue_norm = (category_data[revenue_column] - category_data[revenue_column].min()) / (category_data[revenue_column].max() - category_data[revenue_column].min())
                    category_data['priority_score'] = revenue_norm
                
                # Sort by priority score
                category_data = category_data.sort_values('priority_score', ascending=False)
                
                # Get top categories
                top_categories = category_data.head(3)
                
                # Create result
                result = "# Product Category Prioritization\n\n"
                result += "## Top Categories to Prioritize in Marketing Campaigns\n\n"
                
                for i, row in top_categories.iterrows():
                    result += f"### {row[category_column]}\n"
                    result += f"   * Revenue: ${row[revenue_column]:,.2f}\n"
                    
                    if margin_column and margin_column in df.columns:
                        result += f"   * Margin: {row[margin_column]:.2f}%\n"
                    
                    if growth_column and growth_column in df.columns:
                        result += f"   * Growth: {row[growth_column]:.2f}%\n"
                    
                    result += f"   * Priority Score: {row['priority_score']:.2f}\n"
                    
                    # Add category-specific insights
                    if margin_column and margin_column in df.columns and growth_column and growth_column in df.columns:
                        if row[margin_column] > category_data[margin_column].median() and row[growth_column] > category_data[growth_column].median():
                            result += "   * **Strategy**: Star category with high margin and growth - invest aggressively\n"
                        elif row[margin_column] > category_data[margin_column].median() and row[growth_column] <= category_data[growth_column].median():
                            result += "   * **Strategy**: Cash cow with high margin but lower growth - maintain position\n"
                        elif row[margin_column] <= category_data[margin_column].median() and row[growth_column] > category_data[growth_column].median():
                            result += "   * **Strategy**: Question mark with high growth but lower margin - focus on improving efficiency\n"
                        else:
                            result += "   * **Strategy**: Selected primarily for revenue volume - review pricing strategy\n"
                    else:
                        result += "   * **Strategy**: High revenue category - focus on maintaining market share\n"
                    
                    result += "\n"
                
                # Create visualization: BCG matrix if margin and growth data available
                if margin_column and margin_column in df.columns and growth_column and growth_column in df.columns:
                    plt.figure(figsize=(10, 8))
                    
                    # Scatter plot with bubble size representing revenue
                    # Normalize revenue for bubble size
                    max_bubble_size = 1000
                    min_bubble_size = 50
                    sizes = (category_data[revenue_column] - category_data[revenue_column].min()) / (category_data[revenue_column].max() - category_data[revenue_column].min()) 
                    sizes = sizes * (max_bubble_size - min_bubble_size) + min_bubble_size
                    
                    # Plot
                    scatter = plt.scatter(
                        category_data[growth_column], 
                        category_data[margin_column],
                        s=sizes,
                        alpha=0.6,
                        c=category_data['priority_score'],
                        cmap='viridis'
                    )
                    
                    # Add labels to points
                    for i, row in category_data.iterrows():
                        plt.annotate(
                            row[category_column], 
                            (row[growth_column], row[margin_column]),
                            xytext=(5, 5),
                            textcoords='offset points'
                        )
                    
                    # Add quadrant lines
                    plt.axhline(y=category_data[margin_column].median(), color='gray', linestyle='--', alpha=0.5)
                    plt.axvline(x=category_data[growth_column].median(), color='gray', linestyle='--', alpha=0.5)
                    
                    # Quadrant labels
                    plt.text(category_data[growth_column].max() * 0.9, category_data[margin_column].max() * 0.9, 'STARS', fontsize=12)
                    plt.text(category_data[growth_column].min() * 1.1, category_data[margin_column].max() * 0.9, 'CASH COWS', fontsize=12)
                    plt.text(category_data[growth_column].max() * 0.9, category_data[margin_column].min() * 1.1, 'QUESTION MARKS', fontsize=12)
                    plt.text(category_data[growth_column].min() * 1.1, category_data[margin_column].min() * 1.1, 'DOGS', fontsize=12)
                    
                    plt.title('Product Category Portfolio Analysis')
                    plt.xlabel(f'Growth ({growth_column})')
                    plt.ylabel(f'Margin ({margin_column})')
                    plt.colorbar(scatter, label='Priority Score')
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    
                    # Save figure to buffer
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png')
                    buffer.seek(0)
                    plt.close()
                    
                    # Convert to base64
                    img_str = base64.b64encode(buffer.read()).decode('utf-8')
                
                # Create bar chart of revenue by category
                plt.figure(figsize=(10, 6))
                bars = plt.bar(
                    category_data[category_column].head(10),
                    category_data[revenue_column].head(10),
                    color=[
                        'green' if i < 3 else 'lightgray' 
                        for i in range(len(category_data.head(10)))
                    ]
                )
                plt.title('Revenue by Product Category (Top 10)')
                plt.ylabel(f'Revenue ({revenue_column})')
                plt.xlabel(category_column)
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                
                # Add revenue values on top of bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(
                        bar.get_x() + bar.get_width()/2.,
                        height * 1.01,
                        f'${height:,.0f}',
                        ha='center', 
                        va='bottom',
                        rotation=0
                    )
                
                plt.tight_layout()
                
                # Save figure to buffer
                buffer2 = io.BytesIO()
                plt.savefig(buffer2, format='png')
                buffer2.seek(0)
                plt.close()
                
                # Convert to base64
                img_str2 = base64.b64encode(buffer2.read()).decode('utf-8')
                
                # Strategic recommendations
                result += "### Campaign Recommendations\n\n"
                result += "#### 1. Integrated Campaign Approach\n"
                result += "Design an integrated marketing campaign focusing on the top 3 product categories identified above:\n"
                result += "- **Primary Focus**: Allocate 60% of campaign budget to these three categories\n"
                result += "- **Messaging Strategy**: Highlight unique value propositions of each category\n"
                result += "- **Channel Mix**: Utilize high-ROI channels identified in budget optimization\n\n"
                
                result += "#### 2. Category-Specific Tactics\n"
                
                for i, row in top_categories.iterrows():
                    result += f"**For {row[category_column]}:**\n"
                    
                    if margin_column and margin_column in df.columns and growth_column and growth_column in df.columns:
                        if row[margin_column] > category_data[margin_column].median() and row[growth_column] > category_data[growth_column].median():
                            result += "- Focus on market expansion and acquisition\n"
                            result += "- Highlight premium features and benefits\n"
                            result += "- Invest in brand building for long-term growth\n"
                        elif row[margin_column] > category_data[margin_column].median() and row[growth_column] <= category_data[growth_column].median():
                            result += "- Focus on customer retention and loyalty\n"
                            result += "- Offer bundle promotions with growing categories\n"
                            result += "- Optimize for profitability rather than volume\n"
                        elif row[margin_column] <= category_data[margin_column].median() and row[growth_column] > category_data[growth_column].median():
                            result += "- Focus on volume growth while improving margins\n"
                            result += "- Test price optimization strategies\n"
                            result += "- Emphasize cost-effective digital channels\n"
                        else:
                            result += "- Focus on product differentiation to justify premium\n"
                            result += "- Consider product improvements or repositioning\n"
                            result += "- Target specific high-value customer segments\n"
                    else:
                        result += "- Deploy targeted campaigns to increase category awareness\n"
                        result += "- Leverage cross-selling opportunities with complementary products\n"
                        result += "- Optimize digital marketing funnel for this category\n"
                    
                    result += "\n"
                
                result += "#### 3. Expected Impact\n"
                
                # Estimate revenue impact
                top_cats_revenue = top_categories[revenue_column].sum()
                total_revenue = category_data[revenue_column].sum()
                top_cats_revenue_pct = (top_cats_revenue / total_revenue) * 100
                
                result += f"- These top 3 categories represent ${top_cats_revenue:,.2f} in revenue ({top_cats_revenue_pct:.1f}% of total)\n"
                result += "- Focusing marketing efforts on these categories is expected to yield:\n"
                result += "  * Short-term: 10-15% revenue growth in these categories\n"
                result += "  * Medium-term: 5-8% improvement in overall marketing ROI\n"
                result += "  * Long-term: Stronger market position and improved customer loyalty\n\n"
                
                result += "#### 4. Measurement Framework\n"
                result += "- Track campaign performance weekly with category-specific KPIs\n"
                result += "- Compare performance against historical benchmarks\n"
                result += "- Conduct A/B testing of messaging and offers\n"
                result += "- Adjust budget allocation based on real-time performance data\n"
                
                logger.info(f"prioritize_product_categories completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error in product category prioritization: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def forecast_revenue_impact(table_name: str, channel_column: str, spend_column: str, 
                                  revenue_column: str, optimized_allocations: Dict[str, float] = None) -> str:
            """
            Forecast the expected revenue impact of recommended budget allocations.
            
            Args:
                table_name: Name of the table containing channel performance data
                channel_column: Column name with channel information
                spend_column: Column name with marketing spend data
                revenue_column: Column name with revenue data
                optimized_allocations: Dictionary of channel:budget pairs for optimized allocation
                
            Returns:
                String with forecasted revenue impact
            """
            logger.info(f"Tool called: forecast_revenue_impact")
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name].copy()
                
                # Ensure columns exist
                for col in [channel_column, spend_column, revenue_column]:
                    if col not in df.columns:
                        return f"Column '{col}' not found in table. Available columns: {', '.join(df.columns)}"
                
                # Aggregate data by channel
                channel_data = df.groupby(channel_column).agg({
                    spend_column: 'sum',
                    revenue_column: 'sum'
                }).reset_index()
                
                # If no optimized allocations provided, run the optimizer
                if optimized_allocations is None:
                    logger.info("No optimized allocations provided, running optimization")
                    # Get current total budget
                    total_budget = channel_data[spend_column].sum()
                    
                    # Model elasticity for each channel
                    elasticities = {}
                    for channel in channel_data[channel_column]:
                        channel_spend = channel_data.loc[channel_data[channel_column] == channel, spend_column].values[0]
                        channel_revenue = channel_data.loc[channel_data[channel_column] == channel, revenue_column].values[0]
                        roas = channel_revenue / channel_spend if channel_spend > 0 else 0
                        
                        # Simple elasticity model based on ROAS
                        elasticity = min(0.8, max(0.2, 0.3 + 0.05 * min(roas, 10)))
                        elasticities[channel] = elasticity
                    
                    # Simple ROI-based allocation
                    roas_values = channel_data[revenue_column] / channel_data[spend_column]
                    # Handle infinities and NaN
                    roas_values = roas_values.replace([np.inf, -np.inf], np.nan).fillna(0)
                    
                    # Weight by square root of spend to balance large and small channels
                    weighted_roas = roas_values * np.sqrt(channel_data[spend_column])
                    allocation_weights = weighted_roas / weighted_roas.sum()
                    optimized_allocations = {}
                    for i, row in channel_data.iterrows():
                        channel = row[channel_column]
                        optimized_allocations[channel] = total_budget * allocation_weights.iloc[i]
                else:
                    # Validate optimized allocations
                    for channel in optimized_allocations:
                        if channel not in channel_data[channel_column].values:
                            return f"Channel '{channel}' in optimized allocations not found in data"
                    
                    # Fill in missing channels with current spend
                    for channel in channel_data[channel_column]:
                        if channel not in optimized_allocations:
                            current_spend = channel_data.loc[channel_data[channel_column] == channel, spend_column].values[0]
                            optimized_allocations[channel] = current_spend
                
                # Add optimized allocation to dataframe
                channel_data['optimized_spend'] = channel_data[channel_column].map(optimized_allocations)
                channel_data['spend_change'] = channel_data['optimized_spend'] - channel_data[spend_column]
                channel_data['spend_change_pct'] = (channel_data['spend_change'] / channel_data[spend_column]) * 100
                
                # Calculate current metrics
                channel_data['roas'] = channel_data[revenue_column] / channel_data[spend_column]
                channel_data['roi'] = (channel_data[revenue_column] - channel_data[spend_column]) / channel_data[spend_column]
                
                # Calculate forecasted revenue
                forecasted_revenue = 0
                for i, row in channel_data.iterrows():
                    channel = row[channel_column]
                    current_spend = row[spend_column]
                    current_revenue = row[revenue_column]
                    optimized_spend = row['optimized_spend']
                    
                    # Model elasticity based on ROAS
                    roas = row['roas']
                    elasticity = min(0.8, max(0.2, 0.3 + 0.05 * min(roas, 10)))
                    
                    # Forecasted revenue model: R = current_revenue * (new_spend/current_spend)^elasticity
                    if current_spend > 0:
                        channel_forecasted_revenue = current_revenue * (optimized_spend/current_spend)**elasticity
                    else:
                        # For channels with no current spend, use average ROAS
                        channel_forecasted_revenue = optimized_spend * channel_data['roas'].mean()
                    
                    forecasted_revenue += channel_forecasted_revenue
                    channel_data.at[i, 'forecasted_revenue'] = channel_forecasted_revenue
                
                # Calculate impact metrics
                current_total_revenue = channel_data[revenue_column].sum()
                revenue_increase = forecasted_revenue - current_total_revenue
                revenue_increase_pct = (revenue_increase / current_total_revenue) * 100
                
                # Calculate current and forecasted marketing ROI
                current_total_spend = channel_data[spend_column].sum()
                forecasted_total_spend = channel_data['optimized_spend'].sum()
                
                current_roi = (current_total_revenue - current_total_spend) / current_total_spend
                forecasted_roi = (forecasted_revenue - forecasted_total_spend) / forecasted_total_spend
                
                roi_improvement = forecasted_roi - current_roi
                roi_improvement_pct = (roi_improvement / current_roi) * 100 if current_roi > 0 else 0
                
                # Format results
                result = "# Forecasted Revenue Impact of Budget Optimization\n\n"
                result += "## Summary Impact\n\n"
                result += f"- **Current Total Revenue**: ${current_total_revenue:,.2f}\n"
                result += f"- **Forecasted Revenue**: ${forecasted_revenue:,.2f}\n"
                result += f"- **Revenue Increase**: ${revenue_increase:,.2f} ({revenue_increase_pct:.2f}%)\n\n"
                
                result += f"- **Current Marketing ROI**: {current_roi:.2f} ({current_roi*100:.1f}%)\n"
                result += f"- **Forecasted Marketing ROI**: {forecasted_roi:.2f} ({forecasted_roi*100:.1f}%)\n"
                result += f"- **ROI Improvement**: {roi_improvement:.2f} ({roi_improvement_pct:.1f}%)\n\n"
                
                result += "## Channel-by-Channel Forecast\n\n"
                
                # Create channel breakdown table
                for i, row in channel_data.sort_values('forecasted_revenue', ascending=False).iterrows():
                    channel = row[channel_column]
                    result += f"### {channel}\n\n"
                    result += f"- Current Spend: ${row[spend_column]:,.2f}\n"
                    result += f"- Optimized Spend: ${row['optimized_spend']:,.2f} "
                    
                    if row['spend_change'] > 0:
                        result += f"(+${row['spend_change']:,.2f}, +{row['spend_change_pct']:.1f}%)\n"
                    else:
                        result += f"(${row['spend_change']:,.2f}, {row['spend_change_pct']:.1f}%)\n"
                    
                    result += f"- Current Revenue: ${row[revenue_column]:,.2f}\n"
                    result += f"- Forecasted Revenue: ${row['forecasted_revenue']:,.2f} "
                    
                    rev_change = row['forecasted_revenue'] - row[revenue_column]
                    rev_change_pct = (rev_change / row[revenue_column]) * 100 if row[revenue_column] > 0 else 0
                    
                    if rev_change > 0:
                        result += f"(+${rev_change:,.2f}, +{rev_change_pct:.1f}%)\n"
                    else:
                        result += f"(${rev_change:,.2f}, {rev_change_pct:.1f}%)\n"
                    
                    result += f"- Current ROAS: {row['roas']:.2f}\n"
                    result += f"- Forecasted ROAS: {row['forecasted_revenue']/row['optimized_spend']:.2f}\n\n"
                
                # Create visualization: comparison between current and forecasted revenue
                plt.figure(figsize=(12, 7))
                
                # Sort by current revenue
                sorted_data = channel_data.sort_values(revenue_column, ascending=False)
                
                # Set up the bar positions
                bar_width = 0.35
                x = np.arange(len(sorted_data))
                
                # Create the bars
                plt.bar(x - bar_width/2, sorted_data[revenue_column], bar_width, label='Current Revenue', color='skyblue')
                plt.bar(x + bar_width/2, sorted_data['forecasted_revenue'], bar_width, label='Forecasted Revenue', color='tomato')
                
                # Add labels and title
                plt.xlabel('Channel')
                plt.ylabel('Revenue ($)')
                plt.title('Current vs. Forecasted Revenue by Channel')
                plt.xticks(x, sorted_data[channel_column], rotation=45, ha='right')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save figure to buffer
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                plt.close()
                
                # Convert to base64
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                
                # Add image to result if needed
                # result += f"\n\n![Current vs. Forecasted Revenue](data:image/png;base64,{img_str})\n\n"
                
                # Create pie chart for budget allocation
                plt.figure(figsize=(20, 10))
                
                # Create subplots for current and optimized allocation
                plt.subplot(1, 2, 1)
                plt.pie(channel_data[spend_column], labels=channel_data[channel_column], autopct='%1.1f%%', startangle=90)
                plt.title('Current Budget Allocation')
                
                plt.subplot(1, 2, 2)
                plt.pie(channel_data['optimized_spend'], labels=channel_data[channel_column], autopct='%1.1f%%', startangle=90)
                plt.title('Optimized Budget Allocation')
                
                plt.tight_layout()
                
                # Save figure to buffer
                buffer2 = io.BytesIO()
                plt.savefig(buffer2, format='png')
                buffer2.seek(0)
                plt.close()
                
                # Convert to base64
                img_str2 = base64.b64encode(buffer2.read()).decode('utf-8')
                
                # Add image to result if needed
                # result += f"\n\n![Budget Allocation Comparison](data:image/png;base64,{img_str2})\n\n"
                
                result += "## Implementation Recommendations\n\n"
                result += "1. **Gradual Transition**: Implement budget changes over 1-2 quarters to monitor impact\n"
                result += "2. **A/B Testing**: Test new allocations in limited markets before full rollout\n"
                result += "3. **Weekly Monitoring**: Set up weekly performance tracking to catch any negative trends early\n"
                result += "4. **Seasonality Adjustments**: Adjust allocations seasonally based on historical performance\n"
                result += "5. **Feedback Loop**: Create a system to continuously optimize based on actual performance\n"
                
                logger.info(f"forecast_revenue_impact completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error in revenue impact forecasting: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        def create_comparison_chart(table_name: str, channel_column: str, metric_columns: List[str]) -> str:
            """
            Create a comparison chart for different marketing metrics across channels.
            
            Args:
                table_name: Name of the table containing channel data
                channel_column: Column name with channel information
                metric_columns: List of column names to compare
                
            Returns:
                String with chart in base64 format
            """
            logger.info(f"Tool called: create_comparison_chart")
            try:
                if table_name not in self.dataframes:
                    return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
                
                df = self.dataframes[table_name].copy()
                
                # Ensure columns exist
                for col in [channel_column] + metric_columns:
                    if col not in df.columns:
                        return f"Column '{col}' not found in table. Available columns: {', '.join(df.columns)}"
                
                # Aggregate data by channel
                channel_data = df.groupby(channel_column)[metric_columns].sum().reset_index()
                
                # Create comparison chart
                plt.figure(figsize=(12, 8))
                
                # For each metric, create a subplot
                num_metrics = len(metric_columns)
                rows = (num_metrics + 1) // 2  # Ceiling division to get number of rows
                
                for i, metric in enumerate(metric_columns, 1):
                    plt.subplot(rows, 2, i)
                    
                    # Sort by metric value
                    sorted_data = channel_data.sort_values(metric, ascending=False)
                    
                    # Create bar chart
                    bars = plt.bar(sorted_data[channel_column], sorted_data[metric], color='skyblue')
                    
                    # Add value labels on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                                f'{height:.2f}',
                                ha='center', va='bottom', rotation=0)
                    
                    plt.title(f'{metric} by Channel')
                    plt.xticks(rotation=45, ha='right')
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                
                # Save figure to buffer
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                plt.close()
                
                # Convert to base64
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                
                result = f"# Channel Comparison: {', '.join(metric_columns)}\n\n"
                result += f"![Channel Comparison](data:image/png;base64,{img_str})\n\n"
                
                logger.info(f"create_comparison_chart completed for {table_name}")
                return result
                
            except Exception as e:
                error_msg = f"Error creating comparison chart: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return error_msg
        
        return [
            StructuredTool.from_function(
                func=optimize_budget_allocation,
                name="optimize_budget_allocation",
                description="Optimize marketing budget allocation across channels based on ROI analysis"
            ),
            StructuredTool.from_function(
                func=prioritize_product_categories,
                name="prioritize_product_categories",
                description="Identify and prioritize product categories for upcoming marketing campaigns"
            ),
            StructuredTool.from_function(
                func=forecast_revenue_impact,
                name="forecast_revenue_impact",
                description="Forecast the expected revenue impact of recommended budget allocations"
            ),
            StructuredTool.from_function(
                func=create_comparison_chart,
                name="create_comparison_chart",
                description="Create a comparison chart for different marketing metrics across channels"
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the budget allocation agent."""
        logger.info("Creating budget allocation agent")
        
        # Get data schema
        data_schema = self._get_data_schema()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a marketing budget optimization specialist with expertise in allocation modeling, 
            ROI forecasting, and financial analysis. Your goal is to help marketers optimize their 
            budget allocation to maximize returns and business impact.
            
            Here is the schema of the available data:
            {data_schema}
            
            Focus on:
            1. Optimizing budget allocation across marketing channels based on ROI analysis
            2. Prioritizing product categories for marketing investment
            3. Forecasting revenue impact of recommended budget changes
            4. Providing clear, actionable recommendations with visualizations
            
            You have access to marketing data and can use the following tools:
            - optimize_budget_allocation: Create optimal budget allocation models based on ROI
            - prioritize_product_categories: Identify which product categories to focus on
            - forecast_revenue_impact: Predict revenue outcomes from recommended changes
            - create_comparison_chart: Generate visualizations to support recommendations
            
            When analyzing budget allocations:
            - Consider historical performance data and ROI by channel
            - Balance short-term performance with long-term brand building
            - Account for diminishing returns in high-spend channels
            - Consider constraints like minimum effective spend levels
            - Provide gradual transition plans rather than dramatic shifts
            
            Always provide specific, measurable recommendations with forecasted impact and clear 
            implementation guidance.
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
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True,handle_parsing_errors=True, verbose_errors=True)
    
    def invoke(self, query: str) -> str:
        """Process budget analysis query using direct tool calling."""
        logger.info(f"Analyzing budget query: {query}")
        try:
            # Validate query has required info
            if "table" not in query.lower():
                return "Error: Query must specify target data table"
            
            # Extract table name from query
            import re
            table_match = re.search(r'using\s+(\w+)\s+table', query, re.IGNORECASE)
            table_name = table_match.group(1) if table_match else "Master"
            
            if table_name not in self.dataframes:
                return f"Table '{table_name}' not found. Available tables: {', '.join(self.dataframes.keys())}"
            
            # Get the actual dataframe
            df = self.dataframes[table_name].copy()
            
            # Looking at actual column structure, use the marketing channels directly
            # These are the actual marketing channels in the data
            channels = ['TV', 'Digital', 'Sponsorship', 'Content Marketing', 
                        'Online marketing', 'SEM', 'Radio', 'Other']
                        
            # Remove any columns that don't exist
            channels = [ch for ch in channels if ch in df.columns]
            
            if not channels:
                return "No marketing channel columns found in the data"
                
            # Use GMV as revenue metric
            revenue_col = "gmv"
            if revenue_col not in df.columns:
                return f"Revenue column '{revenue_col}' not found in table"
                
            # For multi-channel analysis, we need to restructure the data
            # Create a result manually with meaningful insights
            result = "# Marketing Budget Optimization Analysis\n\n"
            result += "## Channel Performance Summary\n\n"
            
            # Aggregate total spend by channel
            channel_totals = {}
            total_investment = df["Total Investment"].sum()
            total_gmv = df[revenue_col].sum()
            
            for channel in channels:
                channel_spend = df[channel].sum()
                channel_totals[channel] = channel_spend
                
            # Calculate ROI based on allocation percentages
            result += "### Current Channel Allocation and ROI\n\n"
            result += "| Channel | Current Spend | % of Budget | Estimated ROI |\n"
            result += "|---------|---------------|------------|---------------|\n"
            
            for channel, spend in sorted(channel_totals.items(), key=lambda x: x[1], reverse=True):
                # Estimate channel ROI based on its proportion of spend
                spend_pct = (spend / total_investment) * 100
                # Simple ROI calculation assuming proportional contribution to GMV
                channel_roi = (total_gmv * (spend/total_investment) - spend) / spend * 100
                result += f"| {channel} | ${spend:,.2f} | {spend_pct:.1f}% | {channel_roi:.1f}% |\n"
            
            # Add optimization section
            result += "\n## Optimized Budget Allocation\n\n"
            result += "Based on channel performance analysis, consider the following allocation:\n\n"
            
            # Simple optimization - allocate more to higher ROI channels
            # This is a simplified approach since we don't have actual channel-specific GMV data
            result += "| Channel | Recommended Spend | % Change | Expected Impact |\n"
            result += "|---------|-------------------|----------|----------------|\n"
            
            # Calculate allocation based on simplified ROI (normally would use elasticity models)
            total = sum(channel_totals.values())
            for channel, spend in sorted(channel_totals.items(), key=lambda x: x[1], reverse=True):
                # Higher spend channels get proportionately lower increases to account for diminishing returns
                if spend > total_investment * 0.20:  # Big channels
                    adjustment = 0.90  # Reduce slightly
                elif spend > total_investment * 0.10:  # Medium channels
                    adjustment = 1.05  # Slight increase
                else:  # Small channels
                    adjustment = 1.15  # Larger increase
                    
                new_spend = spend * adjustment
                change_pct = (new_spend - spend) / spend * 100
                result += f"| {channel} | ${new_spend:,.2f} | {change_pct:+.1f}% | "
                
                if change_pct > 0:
                    result += "Increased market reach |\n"
                else:
                    result += "Improved efficiency |\n"
                    
            # Add implementation plan
            result += "\n## Implementation Plan\n\n"
            result += "1. **Gradual Transition**: Implement changes over 2-3 months\n"
            result += "2. **A/B Testing**: Test new allocations in limited markets\n"
            result += "3. **Performance Monitoring**: Weekly review of key metrics\n"
            result += "4. **Channel-Specific KPIs**: Set performance targets for each channel\n"
            result += "5. **Feedback Loop**: Continuously refine based on results\n"
            
            return result
        except Exception as e:
            error_msg = f"Error in budget analysis: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg

def get_budget_agent(llm=None, data_manager=None):
    """Create a budget allocation agent."""
    logger.info("Creating budget agent")
    if llm is None:
        try:
            # Try to get API key from environment variable first
            import os
            api_key = os.environ.get("GROQ_API_KEY")
            
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            llm = ChatGroq(
                api_key=api_key,
                # Overridable since Groq's model catalog/account entitlements change over
                # time -- see https://console.groq.com/docs/models if this 404s.
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
                temperature=0,
                max_retries=5,
                timeout=90
            )
            logger.info("Successfully initialized Groq LLM")
        except Exception as e:
            logger.error(f"Error initializing Groq LLM: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to initialize language model: {str(e)}")
    
    try:
        # Create or get the data manager with the specified data directory
        data_manager = get_data_manager()
        
        # Create the budget agent with the shared data manager
        agent = BudgetAgent(llm, data_manager)
        return agent
    except Exception as e:
        logger.error(f"Error creating budget agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to create budget agent: {str(e)}")


def main():
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found")
        return

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        max_retries=3,
        timeout=30,
        api_key=GROQ_API_KEY
    )
            
    # Initialize agent with proper data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # Create budget agent
    budget_agent = BudgetAgent(llm, data_dir)

    # Modified query using correct column names from Master.csv
    query = """
    Analyze marketing channel performance and recommend budget allocation using Master table:
    - Use channel_name for channels
    - Use marketing_spend for costs 
    - Use revenue for returns

    Provide:
    1. Channel ROI analysis
    2. Optimal budget allocation
    3. Revenue impact forecasts
    4. Implementation plan
    """

    # Run analysis
    result = budget_agent.invoke(query)
    print("\nBudget Analysis Results:")
    print("-" * 50) 
    print(result)


if __name__ == "__main__":
    main()