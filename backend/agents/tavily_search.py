import os
import sys
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.tools import StructuredTool
from tavily import TavilyClient

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Get Tavily API key from environment
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not found in .env file")


class TavilySearchSchema(BaseModel):
    """Schema for Tavily search parameters."""
    query: str

class TavilySearchTool:
    """
    Implements search functionality using the Tavily API.
    
    Features:
    - Advanced search capabilities
    - Configurable result count
    - Structured markdown output
    - Detailed metadata
    """
    
    def __init__(self, max_results: int = 5, search_depth: str = "advanced"):
        """
        Initialize Tavily search tool.
        
        Args:
            max_results: Maximum number of results to return
            search_depth: Depth of search ('basic' or 'advanced')
        """
        self.client = TavilyClient(api_key=TAVILY_API_KEY)
        self.max_results = max_results
        self.search_depth = search_depth

    def search(self, query: str) -> Dict[str, Any]:
        """
        Execute search query and format results.
        
        Args:
            query: Search query string
            
        Returns:
            Dict containing formatted message and metadata
        """
        try:
            # Execute search
            response = self.client.search(
                query, 
                max_results=self.max_results, 
                search_depth=self.search_depth
            )
            results = response.get('results', [])
            
            # Format results in markdown
            message_parts = [f"### Search Results for: {query}\n\n"]
            
            for result in results:
                title = result.get('title', 'No Title')
                url = result.get('url', '')
                content = result.get('content', 'No content available')
                
                message_parts.extend([
                    f"#### {title}\n",
                    f"{content}\n",
                    f"Source: [{url}]({url})\n\n"
                ])
            
            return {
                'message': "".join(message_parts),
                'metadata': {
                    'query': response.get('query', ''),
                    'response_time': response.get('response_time', 0),
                    'result_count': len(results),
                    'source': 'tavily_search'
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to execute Tavily search: {str(e)}"
            print(error_msg)  # or use logger if available
            return {
                'message': f"Error: {error_msg}",
                'metadata': {
                    'query': query,
                    'error': str(e),
                    'source': 'tavily_search'
                }
            }

    def get_tool(self) -> StructuredTool:
        """Get the configured search tool."""
        return StructuredTool(
            name="tavily_search_results_json",
            description="Retrieve current, general, or trending information from web sources using Tavily Search API.",
            func=self.search,
            args_schema=TavilySearchSchema
        )

def get_tavily_search_tool(max_results: int = 5, search_depth: str = "advanced") -> StructuredTool:
    """
    Create and return a Tavily search tool instance.
    
    Args:
        max_results: Maximum number of results to return
        search_depth: Depth of search ('basic' or 'advanced')
    
    Returns:
        StructuredTool: A configured web search tool
    """
    search_tool = TavilySearchTool(max_results=max_results, search_depth=search_depth)
    return search_tool.get_tool()

def main():
    """Test the Tavily search tool."""
    if not TAVILY_API_KEY:
        print("Error: TAVILY_API_KEY not found in .env file. Cannot continue.")
        return
        
    try:
        # Get the search tool
        search_tool = get_tavily_search_tool()
        
        # Test query
        test_query = "What are the latest developments in AI technology?"
        result = search_tool.invoke({"query": test_query})
        
        print("\nSearch Results:")
        print(result['message'])
        print("\nMetadata:")
        print(result['metadata'])
            
    except Exception as e:
        print(f"Error testing search tool: {str(e)}")

if __name__ == "__main__":
    main() 