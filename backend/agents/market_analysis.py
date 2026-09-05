import os
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel
from agents.tavily_search import get_tavily_search_tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import StructuredTool

class MarketAnalysisAgent:
    """Agent that performs market analysis using Tavily search."""
    
    def __init__(self, llm: BaseChatModel = None):
        """
        Initialize the Market Analysis Agent.
        
        Args:
            llm: LLM to use (defaults to ChatGroq if None provided)
        """
        if llm is None:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            # Overridable since Groq's model catalog/account entitlements change over
            # time -- see https://console.groq.com/docs/models if this 404s.
            self.llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0, api_key=api_key)
        else:
            self.llm = llm
            
        # Initialize Tavily search tool
        self.search_tool = get_tavily_search_tool(
            max_results=5,
            search_depth="advanced"
        )
        
        # Create the agent executor
        self.agent_executor = self._create_market_analysis_agent()
    
    def _create_market_analysis_agent(self) -> AgentExecutor:
        """Create the market analysis agent with tools."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a market analysis expert specialized in marketing expenditure analysis.
            Your task is to provide detailed market insights and analysis using web search data.
            
            Use the following methodology:
            
            Question: the input question about market analysis
            Thought: think about what information you need and how to find it
            Action: use the tavily_search_results_json tool to find relevant information
            Action Input: the search query
            Observation: the search results
            ... (this process can repeat multiple times)
            Thought: synthesize the information gathered
            Final Answer: provide a detailed analysis with specific insights
            
            Guidelines for your analysis:
            1. Focus on marketing expenditure and ROI insights
            2. Include relevant statistics and trends
            3. Consider competitor information when available
            4. Provide actionable recommendations
            5. Cite sources when presenting specific data
            6. Structure your response clearly with sections
            7. Highlight key findings and implications
            
            Remember to:
            - Verify information from multiple sources when possible
            - Consider both quantitative and qualitative data
            - Provide context for any statistics or trends
            - Make clear connections to marketing strategy
            """),
            ("human", "Question: {query}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(
            self.llm,
            [self.search_tool],
            prompt
        )
        
        # Create the executor
        return AgentExecutor(
            agent=agent,
            tools=[self.search_tool],
            verbose=True
        )
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Perform market analysis on a given query.
        
        Args:
            query: The question or topic to research
            
        Returns:
            Dict containing analysis results and metadata
        """
        try:
            # Run the analysis
            result = self.agent_executor.invoke({"query": query})
            
            return {
                "analysis": result["output"],
                "metadata": {
                    "query": query,
                    "tool_usage": result.get("intermediate_steps", [])
                }
            }
            
        except Exception as e:
            error_msg = f"Error performing market analysis: {str(e)}"
            print(error_msg)
            return {
                "error": error_msg,
                "metadata": {
                    "query": query,
                    "error_type": type(e).__name__
                }
            }

def get_market_analysis_tool(llm=None) -> StructuredTool:
    """
    Create a market analysis tool that can be used by other agents.
    
    Args:
        llm: Language model to use (defaults to ChatGroq if None)
        
    Returns:
        StructuredTool for market analysis
    """
    agent = MarketAnalysisAgent(llm)
    
    return StructuredTool.from_function(
        name="market_analysis",
        func=agent.analyze,
        description="Analyze market trends, competition, and strategic implications using web search data. "
                   "Provides detailed insights for marketing expenditure analysis."
    )

def main():
    """Test the market analysis agent."""
    agent = MarketAnalysisAgent()
    
    # Test query
    test_query = "What are the current trends in digital marketing ROI for e-commerce platforms?"
    
    result = agent.analyze(test_query)
    
    print(f"\nQuery: {test_query}")
    print("\nAnalysis Results:")
    if "analysis" in result:
        print(result["analysis"])
    else:
        print("Error:", result.get("error", "Unknown error occurred"))
    
    print("\nMetadata:")
    print(result["metadata"])

if __name__ == "__main__":
    main() 