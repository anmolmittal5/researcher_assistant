"""Tavily search tool wrapper using LangChain implementation."""

import os
from langchain_community.tools.tavily_search import TavilySearchResults


def get_tavily_tool() -> TavilySearchResults:
    """Get LangChain Tavily search tool instance."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is required")
    
    return TavilySearchResults(
        tavily_api_key=api_key,
        max_results=5,
    )

