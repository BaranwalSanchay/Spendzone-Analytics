import os
import sys
from typing import Optional, Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool, tool

from agents.sql import get_sql_agent
from agents.market_analysis import MarketAnalysisAgent

class SupervisorAgent:
    """
    A supervisor agent that coordinates between SQL and Market Analysis agents.
    
    This agent decides which specialized agent(s) to use based on the query type.
    """
    
    def __init__(self, llm: BaseChatModel):
        """
        Initialize the supervisor agent with necessary sub-agents.
        
        Args:
            llm: The language model to use for the agent
        """
        self.llm = llm
        
        # Initialize specialized agents
        self.sql_agent, self.db = get_sql_agent(llm)
        self.market_agent = MarketAnalysisAgent(llm)
        
        # Get DB schema for context
        self.db_schema = self.db.get_table_info()
        
        # Create tools for each agent
        self.tools = self._create_tools()
        
        # Create the supervisor agent
        self.agent_executor = self._create_supervisor_agent()

    def _create_tools(self) -> List[StructuredTool]:
        """Create tools for SQL and Market Analysis capabilities."""
        
        def sql_analysis(query: str) -> str:
            """
            Use this tool for questions requiring data analysis from the database.
            Good for questions about specific numbers, trends, or patterns in the data.
            
            Args:
                query (str): The analysis question to be answered using SQL data
                
            Returns:
                str: Analysis results from the SQL database
            """
            try:
                # Get table schema information
                table_names = self.db.get_usable_table_names()
                schema_info = self.db.get_table_info(table_names)
                
                sql_input = (
                    f"Database Schema Information:\n{schema_info}\n\n"
                    f"Question: {query}\n\n"
                    "Please analyze this data and provide insights. Include relevant SQL queries and results."
                )
                return self.sql_agent.invoke({"input": sql_input})
            except Exception as e:
                return f"Error in SQL analysis: {str(e)}"

        def market_analysis(query: str) -> str:
            """
            Use this tool for questions requiring market research, industry trends, or strategic insights.
            Good for questions about market dynamics, competitive analysis, or business strategy.
            
            Args:
                query (str): The analysis question to be answered using market research
                
            Returns:
                str: Market analysis insights
            """
            try:
                
                market_question = (
                    f"For a marketing expenditure analysis at ElectroMart, I need information about: "
                    f"{query}"
                )
                return self.market_agent.analyze(market_question)
            except Exception as e:
                return f"Error in market analysis: {str(e)}"

        return [
            StructuredTool.from_function(
                func=sql_analysis,
                name="sql_analysis",
                description="Use for questions requiring specific data analysis, metrics, or patterns from the database"
            ),
            StructuredTool.from_function(
                func=market_analysis,
                name="market_analysis",
                description="Use for questions about market trends, strategy, or business insights"
            )
        ]

    def _create_supervisor_agent(self) -> AgentExecutor:
        """Create the supervisor agent that coordinates between tools."""
        
        try:
            # Get all available table names
            table_names = self.db.get_usable_table_names()
            
            # Get detailed schema information for each table
            db_info = self.db.get_table_info(table_names)
            
            # Format database schema info
            schema_info = "Available Tables and Their Columns:\n"
            schema_info += db_info
            
        except Exception as e:
            print(f"Error getting schema info: {str(e)}")
            schema_info = "Error retrieving schema information"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are a business analyst coordinating between SQL and Market Analysis tools.

            SQL Analysis Tool:
            - Use for analyzing internal data, metrics, and KPIs
            - Examples: revenue analysis, customer metrics, product performance

            Market Analysis Tool:
            - Use for external insights, competitor analysis, and industry trends
            - Examples: market research, competitive benchmarks, industry standards

            For complex questions:
            1. Start with SQL for internal data
            2. Use Market Analysis for external context
            3. Combine insights into actionable recommendations

            Database Schema:
            {schema_info}
            """),
            ("human", "Question: {input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze a question using the appropriate tool(s).
        
        Args:
            query: The question to analyze
            
        Returns:
            Dict containing the analysis results
        """
        try:
            # Add schema information to the input
            input_with_schema = {
                "input": query
            }
            
            # Run the analysis
            result = self.agent_executor.invoke(input_with_schema)
            
            return {
                "result": result["output"],
                "metadata": {
                    "db_schema": self.db_schema,
                    "tools_used": result.get("intermediate_steps", [])
                }
            }
        except Exception as e:
            return {
                "error": f"Error in analysis: {str(e)}",
                "metadata": {"db_schema": self.db_schema}
            }

def get_supervisor_agent(llm=None):
    """
    Create a supervisor agent for coordinated analysis.
    
    Args:
        llm: Language model to use (defaults to ChatGroq if None)
        
    Returns:
        SupervisorAgent instance
    """
    if llm is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=api_key)

    return SupervisorAgent(llm)

def main():
    """Generate a comprehensive marketing analysis report using the supervisor agent."""
    agent = get_supervisor_agent()
    
    # Define report structure
    report_sections = {
        "Executive Summary": [
            "What was the overall effectiveness of Company's marketing spend over the last year? What key insights were identified from analyzing marketing expenditures and their impact on revenue?",
            "What are the top recommendations for reallocating the marketing budget for the upcoming year?"
        ],
        "Business Context & Problem Statement": [
            "Briefly describe Company and its current market situation. What challenges is Company facing regarding its marketing spend?",
        ],
        "Objectives": [
            "Clearly articulate the primary objectives for this analysis related to marketing expenditure. What key performance indicators (KPIs) and metrics should be analyzed?"
        ],
        "Methodology & Technology Stack": [
            "What methodology and analytical approach should be used for analyzing marketing expenditure effectiveness?",
        ],
        "Data Summary": [
            "Summarize the datasets available for analysis. What insights or types of analysis does each dataset enable?",
        ]
    }
    
    # Generate report
    final_report = "# ElectroMart Marketing Expenditure Analysis Report\n\n"
    
    try:
        for section, questions in report_sections.items():
            print(f"\nProcessing section: {section}")
            final_report += f"## {section}\n\n"
            
            for question in questions:
                print(f"\nAnalyzing question: {question[:100]}...")
                
                # Get analysis from supervisor agent
                result = agent.analyze(question)
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                    final_report += f"### Error Processing Question\n"
                    final_report += f"Question: {question}\n"
                    final_report += f"Error: {result['error']}\n\n"
                else:
                    print("Analysis completed successfully")
                    final_report += f"### Analysis\n"
                    final_report += f"Question: {question}\n\n"
                    final_report += f"Answer: {result['result']}\n\n"
                    
                    # Add tools used for transparency
                    if "metadata" in result and "tools_used" in result["metadata"]:
                        final_report += "Tools Used:\n"
                        for step in result["metadata"]["tools_used"]:
                            final_report += f"- {step[0].tool}\n"
                    final_report += "\n"
                
                print("---\n")
        
        # Save the report to a file
        report_path = "marketing_expenditure_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(final_report)
        
        print(f"\nReport generation completed. Report saved to: {report_path}")
        print("\nReport Preview:")
        print(final_report[:1000] + "...\n")
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")

if __name__ == "__main__":
    main() 