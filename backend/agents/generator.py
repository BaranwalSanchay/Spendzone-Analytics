import os
import sys
import time
import gc
import logging
from typing import Dict, List, Any, Optional
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Import agent generators
from agents.exploration import get_exploration_agent
from agents.sql import get_sql_agent
from agents.roi import get_roi_agent
from agents.budget import get_budget_agent
from agents.kpi import get_kpi_agent
from agents.market_analysis import get_market_analysis_tool
from agents.compiler import CompilerAgent
from utils.data_manager import get_data_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("generator")

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

class SequentialGenerator:
    """
    Sequential report generator that executes agents one by one based on section requirements.
    No parallelization, just simple sequential execution for reliable results.
    """
    
    def __init__(self, llm: BaseChatModel = None, data_path: str = None):
        """
        Initialize the sequential generator with LLM and data path.
        
        Args:
            llm: Language model to use for agents
            data_path: Path to data files
        """
        # Initialize LLM if not provided
        if llm is None:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")

            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-lite",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=gemini_api_key
            )
        else:
            self.llm = llm
            
        # Initialize data manager
        self.data_manager = get_data_manager(data_path)
        logger.info(f"Data manager initialized with path: {data_path}")
        
        # Define section-agent mapping
        self.section_agent_mapping = {
            "executive_summary": ["exploration_agent"],
            "business_context": ["exploration_agent", "market_agent", "sql_agent"],
            "marketing_performance": ["exploration_agent", "sql_agent"],
            "performance_drivers": ["kpi_agent", "sql_agent"],
            "marketing_roi": ["roi_agent", "sql_agent"],
            "budget_allocation": ["budget_agent", "sql_agent"],
            "implementation": ["market_agent"]
        }
        
        # Lazy-loaded agents
        self._agents = {}
        
    def _get_agent(self, agent_name: str):
        """
        Get or initialize an agent by name.
        
        Args:
            agent_name: Name of the agent to initialize
            
        Returns:
            Initialized agent instance
        """
        if agent_name not in self._agents:
            logger.info(f"Initializing {agent_name}...")
            
            if agent_name == "exploration_agent":
                self._agents[agent_name] = get_exploration_agent(self.llm, data_manager=self.data_manager)
            
            elif agent_name == "sql_agent":
                agent, _ = get_sql_agent(self.llm, data_manager=self.data_manager)
                self._agents[agent_name] = agent
            
            elif agent_name == "roi_agent":
                self._agents[agent_name] = get_roi_agent(self.llm, data_manager=self.data_manager)
            
            elif agent_name == "budget_agent":
                self._agents[agent_name] = get_budget_agent(self.llm, data_manager=self.data_manager)
            
            elif agent_name == "kpi_agent":
                self._agents[agent_name] = get_kpi_agent(self.llm, data_manager=self.data_manager)
            
            elif agent_name == "market_agent":
                self._agents[agent_name] = get_market_analysis_tool(self.llm)
            
            elif agent_name == "compiler_agent":
                self._agents[agent_name] = CompilerAgent(self.llm)
            
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
                
        return self._agents[agent_name]
    
    def analyze_section(self, question: str, section: str) -> Dict[str, Any]:
        """
        Analyze a question for a specific section by sequentially executing the required agents.
        
        Args:
            question: The question to analyze
            section: Report section name
            
        Returns:
            Dictionary with analysis results and metadata
        """
        start_time = time.time()
        logger.info(f"Starting analysis for section '{section}' with question: {question}")
        
        try:
            # Get the list of agents needed for this section
            agents_needed = self.section_agent_mapping.get(section, [])
            if not agents_needed:
                return {
                    "error": f"No agents defined for section: {section}",
                    "metadata": {"section": section, "execution_time": 0}
                }
            
            logger.info(f"Section '{section}' requires these agents: {', '.join(agents_needed)}")
            
            # Run each agent sequentially and collect results
            results = {}
            
            for agent_name in agents_needed:
                agent_start_time = time.time()
                logger.info(f"Running {agent_name} for section '{section}'...")
                
                try:
                    # Get the agent instance
                    agent = self._get_agent(agent_name)
                    
                    # Different agents have different invocation patterns
                    if agent_name == "exploration_agent":
                        result = agent.analyze(question)
                    elif agent_name == "market_agent":
                        result = agent.invoke(question)
                    elif agent_name == "compiler_agent":
                        result = agent.compile(question)
                    elif agent_name == "sql_agent":
                        result = agent.invoke(question + "Answer the question based on the data in the database. Do not perform over analysis. Perform only the analysis that is required. Please find the database schema: " + self.data_manager.get_schema_info())
                    else:
                        result = agent.invoke(question)
                    
                    # Store results
                    results[agent_name] = result
                    
                    logger.info(f"{agent_name} completed in {time.time() - agent_start_time:.2f} seconds")
                    
                    # Give the system a moment to breathe between agents
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error running {agent_name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    results[agent_name] = {"error": str(e)}
            
            # Run compiler to integrate results
            compiler = self._get_agent("compiler_agent")
            
            # Create a state dictionary similar to what the compiler expects
            compilation_state = {
                "current_section": section,
                "current_question": question
            }
            
            # Add results from each agent to the state
            for agent_name, result in results.items():
                if agent_name == "exploration_agent":
                    compilation_state["exploration_results"] = result
                elif agent_name == "sql_agent":
                    compilation_state["sql_results"] = result
                elif agent_name == "roi_agent":
                    compilation_state["roi_results"] = result
                elif agent_name == "budget_agent":
                    compilation_state["budget_results"] = result
                elif agent_name == "kpi_agent":
                    compilation_state["kpi_results"] = result
                elif agent_name == "market_agent":
                    compilation_state["market_results"] = result
            
            # Compile the final answer
            final_answer = compiler.compile(compilation_state)
            
            # Free up memory
            gc.collect()
            
            execution_time = time.time() - start_time
            logger.info(f"Section '{section}' analysis completed in {execution_time:.2f} seconds")
            
            return {
                "result": final_answer,
                "metadata": {
                    "section": section,
                    "agents_used": agents_needed,
                    "execution_time": execution_time
                }
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error analyzing section '{section}': {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "error": f"Error in analysis: {str(e)}",
                "metadata": {
                    "section": section,
                    "attempted_agents": self.section_agent_mapping.get(section, []),
                    "execution_time": execution_time
                }
            }
    
    def generate_report(self, sections_and_questions: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a full report by analyzing all provided sections.
        
        Args:
            sections_and_questions: Dictionary mapping section names to questions
            
        Returns:
            Dictionary with results for each section and overall metadata
        """
        start_time = time.time()
        logger.info(f"Starting report generation with {len(sections_and_questions)} sections")
        
        report_results = {}
        errors = []
        
        for section, question in sections_and_questions.items():
            section_start_time = time.time()
            logger.info(f"Processing section: {section}")
            
            try:
                # Analyze the section
                result = self.analyze_section(question, section)
                
                # Store results
                report_results[section] = result.get("result", "")
                
                # Check for errors
                if "error" in result:
                    errors.append(f"Error in {section}: {result['error']}")
                
                section_time = time.time() - section_start_time
                logger.info(f"Section '{section}' completed in {section_time:.2f} seconds")
                
                # Pause between sections to avoid rate limiting
                if list(sections_and_questions.keys()).index(section) < len(sections_and_questions) - 1:
                    delay = 5
                    logger.info(f"Waiting {delay} seconds before next section...")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error processing section '{section}': {str(e)}")
                logger.error(traceback.format_exc())
                errors.append(f"Error in {section}: {str(e)}")
                report_results[section] = f"Error generating content: {str(e)}"
        
        total_time = time.time() - start_time
        logger.info(f"Report generation completed in {total_time:.2f} seconds")
        
        return {
            "report_data": report_results,
            "metadata": {
                "total_sections": len(sections_and_questions),
                "successful_sections": len(sections_and_questions) - len(errors),
                "errors": errors,
                "execution_time": total_time
            }
        }

def main():
    """Test the sequential generator with a sample question."""
    try:
        # Initialize generator
        generator = SequentialGenerator()
        
        # Test with a single question
        result = generator.analyze_section(
            "What is the total revenue and how has it changed over time?",
            "executive_summary"
        )
        
        print("\nAnalysis Result:")
        print("="*80)
        if "result" in result:
            print(result["result"])
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("\nMetadata:")
        for key, value in result.get("metadata", {}).items():
            print(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 