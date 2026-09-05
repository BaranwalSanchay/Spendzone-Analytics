import pandas as pd
import os
import sys
import io
from contextlib import redirect_stdout
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool, tool

# Determine paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "..", "data", "Customers_Orders_Data.csv")

# Load the data
def load_dataframe():
    """
    Load the customer orders data into a pandas DataFrame.
    
    Returns:
        pandas DataFrame with customer orders data
    """
    try:
        df = pd.read_csv(data_path)
        print(f"DataFrame loaded from {data_path} with shape {df.shape}")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Could not find Customers_Orders_Data.csv at {data_path}. "
            "Please ensure the file exists in the 'data' directory."
        )

class PandasAnalyst:
    """
    A class that provides pandas data analysis capabilities using LLM and Python execution.

    Args:
        llm (BaseChatModel): The language model to use for analysis

    Returns:
        None
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.df = load_dataframe()
        
        # Set up the Python execution 
        self.python_tool = self._create_python_tool()

    def _execute_python_safely(self, code: str) -> Any:
        """
        Execute Python code safely and return the result.
        
        Args:
            code (str): Python code to execute
            
        Returns:
            Any: The result of the execution
        """
        # Remove any return statements and extract the variable being returned
        return_var = None
        if "return " in code:
            lines = code.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith("return "):
                    return_var = line.strip()[7:].strip()  # Extract var name after "return "
                    lines[i] = f"# {line}"  # Comment out the return line
            code = '\n'.join(lines)
        
        # Create a namespace with pandas, numpy and the dataframe
        namespace = {
            'pd': pd,
            'df': self.df,
            'np': __import__('numpy'),
            'plt': __import__('matplotlib.pyplot'),
            'sns': __import__('seaborn')
        }
        
        # Capture stdout
        buffer = io.StringIO()
        result = None
        
        try:
            # First try to see if the code is a simple expression that returns a value
            try:
                with redirect_stdout(buffer):
                    eval(code, namespace, {'df': self.df})
            except SyntaxError:
                # If it's not a simple expression, execute as statements
                with redirect_stdout(buffer):
                    exec(code, namespace)
                    
                    # If we found a return statement earlier, get that variable
                    if return_var:
                        if return_var in namespace:
                            result = namespace[return_var]
                    # Otherwise look for a result variable
                    elif 'result' in namespace:
                        result = namespace['result']
        
            # Capture any print output
            stdout_capture = buffer.getvalue()
            
            # If there's no result but there is stdout, use that
            if result is None and stdout_capture:
                return stdout_capture
                
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            print(error_msg)
            return error_msg

    def _create_python_tool(self):
        """Create a Python execution tool without using PythonAstREPLTool."""
        
        def execute_code(code: str) -> str:
            # Execute the Python code
            result = self._execute_python_safely(code)
            print(result)
            
            # Format DataFrame results for better readability
            if isinstance(result, pd.DataFrame):
                if len(result) > 10:
                    # Show only first 10 rows for large dataframes
                    result_display = result.head(10).to_markdown()
                    return f"{result_display}\n... ({len(result) - 10} more rows)"
                else:
                    return result.to_markdown()
            
            # Handle dictionaries with mixed types
            elif isinstance(result, dict):
                output_parts = ["Results:"]
                for key, value in result.items():
                    if isinstance(value, pd.DataFrame):
                        df_output = value.to_markdown() if len(value) <= 10 else f"{value.head(10).to_markdown()}\n... ({len(value) - 10} more rows)"
                        output_parts.append(f"\n{key}:\n{df_output}")
                    else:
                        output_parts.append(f"\n{key}: {str(value)}")
                return "\n".join(output_parts)
            
            # For other types, convert to string
            return str(result)
        
        return StructuredTool.from_function(
            name="execute_python",
            func=execute_code,
            description="Execute Python code to analyze a pandas DataFrame. The DataFrame is already loaded as 'df'. "
                       "Use this tool to run pandas, numpy, matplotlib, or seaborn code for data analysis."
        )

    def get_pandas_tool(self):
        # Create the agent using the tools
        agent_executor = self.create_pandas_analysis_agent()

        def analyze_data(query: str, context: Optional[str] = None):
            """Analyze data using pandas with the given query and optional context."""
            df_info = f"""
DataFrame Information:
- Shape: {self.df.shape}
- Columns: {', '.join(self.df.columns)}
- Sample data (first 5 rows):
{self.df.head().to_markdown()}
            """
            
            if context:
                chain_input = {
                    "query": query,
                    "df_info": df_info,
                    "context": context
                }
            else:
                chain_input = {
                    "query": query,
                    "df_info": df_info
                }
            
            return {
                "message": agent_executor.invoke(chain_input)["output"],
                "metadata": {"dataframe_shape": str(self.df.shape)}
            }

        return StructuredTool.from_function(
            name="pandas_analyst",
            func=analyze_data,
            description="A data analysis expert that uses pandas to analyze datasets. "
                       "Provide a question about the data and get a detailed analysis using Python code."
        )

    def create_pandas_analysis_agent(self):
        model = self.llm
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a data analysis expert specializing in pandas, numpy, and data visualization.
            You have access to a pandas DataFrame called 'df'.
            
            Your task is to write Python code to analyze the data and answer the user's query.
            
            {df_info}
            
            Use the following methodology to analyze the data:

            Question: the input question or request about the data
            Thought: you should always think about what approach to take
            Action: the action to take (use execute_python to run code)
            Action Input: the Python code to execute
            Observation: the result of the code execution
            ... (this process can repeat multiple times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question with clear explanations

            When writing Python code:
            1. Use efficient pandas and numpy operations
            2. Include comments to explain your approach
            3. Handle potential errors or edge cases
            4. Use proper data visualization with matplotlib or seaborn when relevant
            5. Don't use return statements - always print the actual data or results
            6. Structure your code correctly to get the correct indentation

            After generating each result, think about whether you need more analysis steps
            to fully answer the question or if you can provide the final answer.
            """),
            ("human", "Question: {query}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        # Create the agent using the tools
        agent = create_tool_calling_agent(model, [self.python_tool], prompt)

        # Create the AgentExecutor
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=[self.python_tool], 
            verbose=True
        )

        return agent_executor

# Function to get the pandas analyst
def get_pandas_agent(llm=None):
    """
    Create a pandas analyst for advanced data analysis.
    
    Args:
        llm: Language model to use for the agent (if None, creates a ChatGroq instance)
        
    Returns:
        PandasAnalyst tool and the DataFrame
    """
    if llm is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        # Overridable since Groq's model catalog/account entitlements change over time --
        # see https://console.groq.com/docs/models if this 404s.
        llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0, api_key=api_key)

    analyst = PandasAnalyst(llm)
    return analyst.get_pandas_tool(), analyst.df

def main():
    """Test the pandas analyst with a simple query."""
    tool, df = get_pandas_agent()
    result = tool.invoke("What is the total sum of the 'GMV' column? Also calculate the average GMV by payment method.")
    print(f"Result:\n{result['message']}")

if __name__ == "__main__":
    main() 