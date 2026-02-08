"""
LangChain tools for the agent
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langchain_core.tools import tool

from langchain_community.tools.tavily_search import TavilySearchResults

from app.services.rag_service import rag_kb
from app.core.config import settings


@tool
def search_local_knowledge(query: str, doc_type: str = None, version: str = None, k: int = None) -> str:
    """
    Search the local Watch OS 26 knowledge base for relevant information.
    This should be your FIRST choice for answering questions about Watch OS 26.
    Always use version filter if any specific version is mentioned

    Args:
        query: The search query
        doc_type: Optional filter - 'user_guide' or 'release_notes'
        version: Optional version filter for release notes (e.g., '26.3','26.2')
        k: Number of results to return

    Returns:
        Relevant information from the knowledge base
    """
    if not rag_kb.vectorstore:
        return "Knowledge base not available. Please use web search instead."
    
    try:
        k = k or settings.DEFAULT_SEARCH_RESULTS
        
        # Search with appropriate filters
        if version:
            results = rag_kb.search_by_version(query, version, k=k)
        elif doc_type:
            results = rag_kb.search_by_doc_type(query, doc_type, k=k)
        else:
            results = rag_kb.search(query, k=k)
        
        if not results:
            return "No relevant information found in knowledge base. Consider using web search."
        
        # Format results
        formatted = "=== From Watch OS 26 Knowledge Base ===\n\n"
        
        for i, result in enumerate(results[:k], 1):
            metadata = result['metadata']
            content = result['content']
            
            formatted += f"[Source {i}] "
            
            if metadata.get('doc_type') == 'release_notes':
                formatted += f"Watch OS {metadata.get('version', 'N/A')} Release Notes"
                if metadata.get('section'):
                    formatted += f" - {metadata['section']}"
            else:
                formatted += metadata.get('title', 'Untitled')
            
            formatted += "\n"
            formatted += f"Type: {metadata.get('doc_type', 'N/A')}\n"
            formatted += f"URL: {metadata.get('url', 'N/A')}\n"
            
            if metadata.get('total_chunks', 1) > 1:
                formatted += f"Part: {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks')}\n"
            
            formatted += f"\nContent:\n{content}\n"
            formatted += "-" * 60 + "\n\n"
        
        return formatted
    
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


@tool
def fetch_webpage(url: str) -> str:
    """
    Fetch and extract text content from a web page.
    Use this when you need more details from a specific URL found in search results.
    
    Args:
        url: The URL of the webpage to fetch
        
    Returns:
        The extracted text content of the webpage
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return f"Error: Invalid URL format: {url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 3000:
            text = text[:3000] + "...\n[Content truncated for length]"
        
        return f"Content from {url}:\n\n{text}"
        
    except requests.Timeout:
        return f"Error: Request timed out while fetching {url}"
    except requests.RequestException as e:
        return f"Error fetching webpage: {str(e)}"
    except Exception as e:
        return f"Error parsing webpage: {str(e)}"
    


web_search_tool = TavilySearchResults(
    max_results=settings.WEB_SEARCH_MAX_RESULTS,
    search_depth=settings.WEB_SEARCH_DEPTH,
    api_key=settings.TAVILY_API_KEY
)
