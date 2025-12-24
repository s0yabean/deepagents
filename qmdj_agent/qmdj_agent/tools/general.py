"""General utility tools for the QMDJ agent."""

from langchain_core.tools import tool
from datetime import datetime
import httpx
from tavily import TavilyClient
from markdownify import markdownify

# ==============================================================================
# Time Utility Tools
# ==============================================================================

@tool(parse_docstring=True)
def get_current_time() -> str:
    """Get the current date and time in ISO 8601 format for chart generation.
    
    Use this tool to get the current timestamp before calling qmdj_chart_api.
    The returned time is explicitly converted to GMT+8 (Beijing Time).
    """
    from datetime import datetime, timedelta, timezone
    
    # Get current UTC time
    now_utc = datetime.now(timezone.utc)
    
    # Convert to GMT+8 (Beijing Time)
    beijing_time = now_utc + timedelta(hours=8)
    
    return beijing_time.strftime("%Y-%m-%dT%H:%M:%S")

# ==============================================================================
# Web Search Tool (Context Advisor)
# ==============================================================================

def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """Fetch and convert webpage content to markdown."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        html_content = response.text
        markdown_content = markdownify(html_content, heading_style="ATX")
        # Limit content length
        return markdown_content[:3000] if len(markdown_content) > 3000 else markdown_content
    except Exception as e:
        return f"Error fetching content: {str(e)}"

@tool(parse_docstring=True)
def tavily_search(query: str, max_results: int = 2) -> str:
    """Search the web for information to provide external context and evidence.
    
    Use this to find real-world data, news, trends, or research that relates to
    the user's question. This grounds QMDJ readings with objective evidence.
    
    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 2)
    """
    try:
        # Lazy initialization of Tavily client (only when search is called)
        tavily_client = TavilyClient()
        
        # Use Tavily to discover URLs
        search_results = tavily_client.search(
            query,
            max_results=max_results,
            topic="general"
        )
        
        # Fetch full content for each URL
        result_texts = []
        for result in search_results.get("results", []):
            url = result["url"]
            title = result["title"]
            
            # Fetch webpage content
            content = fetch_webpage_content(url)
            
            result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
            result_texts.append(result_text)
        
        # Format final response
        response = f"""🔍 Found {len(result_texts)} result(s) for '{query}':

{chr(10).join(result_texts)}"""
        
        return response
    except Exception as e:
        return f"Search error: {str(e)}. Please try a different query."

# ==============================================================================
# Reasoning Tool
# ==============================================================================

@tool(parse_docstring=True)
def reflect_on_reading(reflection: str) -> str:
    """Tool for strategic reflection and reasoning during analysis.

    Use this to pause and think through interpretations, conflicts, and decisions.

    Args:
        reflection: Your detailed reflection on the analysis
    """
    return f"💭 Reflection recorded: {reflection}"
