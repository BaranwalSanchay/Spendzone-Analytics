from typing import Dict, Any, Optional, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Define the expected state structure for validation
class AgentState(BaseModel):
    """Structure for the state passed to the compiler agent"""
    messages: list = Field(default_factory=list, description="Chat messages")
    current_section: str = Field(description="The current report section being compiled")
    current_question: str = Field(description="The question being analyzed")
    exploration_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from exploration agent")
    sql_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from SQL agent")
    roi_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from ROI agent")
    budget_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from budget agent")
    kpi_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from KPI agent")
    market_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from market analysis")
    final_answer: str = Field(default="", description="The final compiled answer")

class CompilerAgent:
    """Agent that compiles results from multiple agents into a coherent report section."""
    
    def __init__(self, llm: BaseChatModel = None):
        """
        Initialize the Compiler Agent.
        
        Args:
            llm: LLM to use (defaults to ChatGroq if None provided)
        """
        if llm is None:
            self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key = GROQ_API_KEY)
        else:
            self.llm = llm
    
    def compile(self, state: Union[Dict[str, Any], AgentState]) -> str:
        """
        Compile results from multiple agents into a coherent answer.
        
        Args:
            state: The state containing results from all agents (dict or AgentState)
            
        Returns:
            String containing the compiled report section
        """
        try:
            # Handle both dictionary and AgentState objects
            # If it's a dictionary, convert to a normalized dictionary structure
            if isinstance(state, dict):
                current_section = state.get("current_section", "")
                current_question = state.get("current_question", "")
                exploration_results = state.get("exploration_results", {})
                sql_results = state.get("sql_results", {})
                roi_results = state.get("roi_results", {})
                budget_results = state.get("budget_results", {})
                kpi_results = state.get("kpi_results", {})
                market_results = state.get("market_results", {})
            else:
                # It's an AgentState object, use attribute access
                current_section = state.current_section
                current_question = state.current_question
                exploration_results = state.exploration_results
                sql_results = state.sql_results
                roi_results = state.roi_results
                budget_results = state.budget_results
                kpi_results = state.kpi_results
                market_results = state.market_results
            
            # Create the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                You are an expert FORMAL report compiler specializing in marketing analysis reports. 
                Your task is to compile and synthesize information from multiple specialized agents 
                into a coherent, paragraph for section {current_section} in the report. Do not include negetive or uncertain or personal recommendation and drawbacks of analysis. Only include the analysis and findings and content for the section and not a generalized answer. 
                
                Guidelines for compilation:
                
                1. Current Section Context: 
                   - The report section you're compiling is: {current_section}
                   - Each section has specific requirements and focus areas
                
                2. Question Focus:
                   - The specific analysis question is: {current_question}
                   - Ensure your compilation complements the question and the section directly or indirectly.
                 
                 """),
                ("human", """
                Section: {current_section}
                Question: {current_question}
                
                Available Agent Results:
                
                Exploration Agent Results:
                {exploration_results}
                
                SQL Agent Results:
                {sql_results}
                
                ROI Agent Results:
                {roi_results}
                
                Budget Agent Results:
                {budget_results}
                
                KPI Agent Results:
                {kpi_results}
                
                Market Agent Results:
                {market_results}
                
                Please compile these results into a coherent report section that addresses the question of that section.
                """),
                ("system", """"
                
                3. Compilation Guidelines:
                   - Make sure it is a formal company report and doesn't contain your recommedations, It should only have the backed data insights.
                   - Include the data, results and statisticss from all the other Agents in a formal way.
                
                4. Section-Specific Focus:
                   - Executive Summary: High-level insights and key findings
                   - Business Context: Market backdrop and company positioning
                   - Marketing Performance: Channel and campaign effectiveness
                   - Performance Drivers: Factors influencing marketing outcomes along with the data
                   - Marketing ROI: Return on investment analysis across channels along with ROIs of each channel and insights from ROI agent
                   - Budget Allocation: Optimization recommendations along with the stats from the Budget agent
                   - Implementation: Actionable next steps
                
                Format your response as a professional report section with appropriate 
                headings, bullet points, and data visualization descriptions when relevant.
                """)
            ])
            
            # Process any empty results to avoid confusion
            processed_exploration = exploration_results if exploration_results else "No results available"
            processed_sql = sql_results if sql_results else "No results available"
            processed_roi = roi_results if roi_results else "No results available"
            processed_budget = budget_results if budget_results else "No results available"
            processed_kpi = kpi_results if kpi_results else "No results available"
            processed_market = market_results if market_results else "No results available"
            
            # Generate the response
            response = self.llm.invoke(prompt.format(
                current_section=current_section,
                current_question=current_question,
                exploration_results=processed_exploration,
                sql_results=processed_sql,
                roi_results=processed_roi,
                budget_results=processed_budget,
                kpi_results=processed_kpi,
                market_results=processed_market
            ))
            
            return response.content
            
        except Exception as e:
            error_msg = f"Error compiling report section: {str(e)}"
            print(error_msg)
            return error_msg
    
    def invoke(self, state: Dict[str, Any]) -> str:
        """
        Invoke the compiler agent - this is a compatibility wrapper for the LangGraph workflow.
        
        Args:
            state: The state dictionary from the workflow
            
        Returns:
            String containing the compiled report section
        """
        # Directly pass the state dictionary to compile method
        # No need for conversion since compile handles both dict and AgentState
        return self.compile(state)

def get_compiler_agent(llm=None) -> CompilerAgent:
    """
    Create a compiler agent that combines results from other agents.
    
    Args:
        llm: Language model to use (defaults to ChatGroq if None)
        
    Returns:
        CompilerAgent instance
    """
    return CompilerAgent(llm)

def main():
    """Test the compiler agent."""
    agent = CompilerAgent()
    
    # Create a test state
    test_state = {
        "messages": [],
        "current_section": "marketing_roi",
        "current_question": "What is the ROI of our digital marketing channels?",
        "exploration_results": "Data shows increasing investment in digital channels over the past year.",
        "sql_results": "Digital channel spending: Search $50K, Social $75K, Display $30K",
        "roi_results": "Search: 3.2 ROI, Social: 2.1 ROI, Display: 1.4 ROI",
        "budget_results": "Recommend increasing Search budget by 15% and reducing Display by 10%",
        "kpi_results": "CTR improved 15% across Search campaigns",
        "market_results": "Industry average ROI for Search is 2.7, we're outperforming by 18.5%",
        "final_answer": ""
    }
    
    result = agent.invoke(test_state)
    
    print("\nCompiled Report Section:")
    print(result)

if __name__ == "__main__":
    main() 