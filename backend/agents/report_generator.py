from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage
import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.exploration import get_exploration_agent
from agents.sql import get_sql_agent
from agents.roi import get_roi_agent
from agents.budget import get_budget_agent
from agents.kpi import get_kpi_agent
from agents.market_analysis import get_market_analysis_tool
from agents.compiler import get_compiler_agent
import os
from langchain_groq import ChatGroq
from utils.data_manager import get_data_manager
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Define state for our graph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "Chat messages"]
    current_section: str
    current_question: str
    exploration_results: Dict
    sql_results: Dict
    roi_results: Dict
    budget_results: Dict
    kpi_results: Dict
    market_results: Dict
    final_answer: str

class SupervisorAgent:
    def __init__(self, llm, data_path=None):
        self.llm = llm
        
        # Initialize the data manager for all agents to share
        self.data_manager = get_data_manager(data_path)
        
        # Initialize all agents with the shared data manager
        self.exploration_agent = get_exploration_agent(llm, data_manager=self.data_manager)
        self.sql_agent, db = get_sql_agent(llm)  # SQL agent uses its own database
        self.roi_agent = get_roi_agent(llm, data_manager=self.data_manager)
        self.budget_agent = get_budget_agent(llm, data_manager=self.data_manager)
        self.kpi_agent = get_kpi_agent(llm, data_manager=self.data_manager)
        self.market_agent = get_market_analysis_tool(llm)  # Market agent uses web search
        self.compiler_agent = get_compiler_agent(llm)
        
        # Define section-agent mapping
        self.section_agent_mapping = {
            "executive_summary": ["exploration_agent"],
            "business_context": ["exploration_agent", "market_agent", "sql_agent"],
            "marketing_performance": ["exploration_agent", "sql_agent"],
            "performance_drivers": ["kpi_agent", "sql_agent"],
            "marketing_roi": ["roi_agent", "sql_agent"],
            "budget_allocation": ["sql_agent"],
            "implementation": ["market_agent"]
        }
        
        # Create the workflow graph
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow with parallel agent execution."""
        
        workflow = StateGraph(AgentState)
        
        def supervisor(state: AgentState) -> Dict[str, Any]:
            """Supervisor agent that initiates parallel processing."""
            # Simply pass the state to all agents
            return state

        # Node functions for each agent
        def run_exploration(state: AgentState) -> Dict[str, Any]:
            """Run data exploration analysis"""
            if "exploration_agent" in self.section_agent_mapping[state["current_section"]]:
                result = self.exploration_agent.analyze(state["current_question"])
                state["exploration_results"] = result
                return state
            
        def run_sql(state: AgentState) -> Dict[str, Any]:
            """Run SQL analysis"""
            if "sql_agent" in self.section_agent_mapping[state["current_section"]]:
                result = self.sql_agent.invoke(state["current_question"])
                state["sql_results"] = result
                return state

        def run_roi(state: AgentState) -> Dict[str, Any]:
            """Run ROI analysis"""
            if "roi_agent" in self.section_agent_mapping[state["current_section"]]:
                result = self.roi_agent.invoke(state["current_question"])
                state["roi_results"] = result
                return state

        def run_budget(state: AgentState) -> Dict[str, Any]:
            """Run budget allocation analysis"""
            if "budget_agent" in self.section_agent_mapping[state["current_section"]]:
                result = self.budget_agent.invoke(state["current_question"])
                state["budget_results"] = result
                return state

        def run_kpi(state: AgentState) -> Dict[str, Any]:
            """Run KPI analysis"""
            if "kpi_agent" in self.section_agent_mapping[state["current_section"]]:
                result = self.kpi_agent.invoke(state["current_question"])
                state["kpi_results"] = result
                return state

        def run_market(state: AgentState) -> Dict[str, Any]:
            """Run market analysis"""
            if "market_agent" in self.section_agent_mapping[state["current_section"]]:
                result = self.market_agent.run(state["current_question"])
                state["market_results"] = result
                return state


        def compile_results(state: AgentState) -> Dict[str, Any]:
            """Compile all results into final answer"""
            # Collect results from all agents
            result = self.compiler_agent.invoke(state)
            state["final_answer"] = result
            return state

        # Add nodes to workflow
        workflow.set_entry_point("supervisor")
        workflow.add_node("supervisor", supervisor)
        workflow.add_node("exploration", run_exploration)
        workflow.add_node("sql", run_sql)
        workflow.add_node("roi", run_roi)
        workflow.add_node("budget", run_budget)
        workflow.add_node("kpi", run_kpi)
        workflow.add_node("market", run_market)
        workflow.add_node("compiler", compile_results)

        # Define parallel execution paths
        workflow.add_edge("supervisor", "exploration")
        workflow.add_edge("supervisor", "sql")
        workflow.add_edge("supervisor", "roi")
        workflow.add_edge("supervisor", "budget")
        workflow.add_edge("supervisor", "kpi")
        workflow.add_edge("supervisor", "market")
        
        workflow.add_edge("exploration", "compiler")
        workflow.add_edge("sql", "compiler")
        workflow.add_edge("roi", "compiler")
        workflow.add_edge("budget", "compiler")
        workflow.add_edge("kpi", "compiler")
        workflow.add_edge("market", "compiler")
        
        workflow.add_edge("compiler", END)

        
        return workflow

    def analyze(self, question: str, section: str) -> Dict[str, Any]:
        """
        Analyze a question using multiple agents in parallel based on section.
        
        Args:
            question: The question to analyze
            section: The report section this question belongs to
            
        Returns:
            Dict containing the analysis results
        """
        try:
            # Initialize state
            initial_state = AgentState(
                messages=[],
                current_section=section,
                current_question=question,
                exploration_results={},
                sql_results={},
                roi_results={},
                budget_results={},
                kpi_results={},
                market_results={},
                final_answer=""
            )
            chain = self.workflow.compile()
            # Run the workflow
            result = chain.invoke(initial_state)
            
            return {
                "result": result["final_answer"],
                "metadata": {
                    "section": section,
                    "agents_used": self.section_agent_mapping[section]
                }
            }
            
        except Exception as e:
            return {
                "error": f"Error in analysis: {str(e)}",
                "metadata": {
                    "section": section,
                    "attempted_agents": self.section_agent_mapping.get(section, [])
                }
            }
        

def main():
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.getenv("GROQ_API_KEY"))
    report_generator = SupervisorAgent(llm)
    report_generator.analyze("What is the total revenue for the year?", "executive_summary")

if __name__ == "__main__":
    main()