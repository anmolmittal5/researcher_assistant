"""Unit tests for Tavily tool."""

import pytest
import os
from unittest.mock import Mock, patch
from research_assistant.tools.tavily import get_tavily_tool


@pytest.mark.unit
class TestTavilyToolInitialization:
    """Test Tavily tool initialization."""
    
    def test_get_tavily_tool_success(self, mock_env_vars):
        """Test successful Tavily tool initialization."""
        with patch('research_assistant.tools.tavily.TavilySearchResults') as mock_tavily:
            mock_instance = Mock()
            mock_tavily.return_value = mock_instance
            
            tool = get_tavily_tool()
            
            assert tool is not None
            mock_tavily.assert_called_once()
            # Verify API key was used
            call_kwargs = mock_tavily.call_args[1]
            assert "tavily_api_key" in call_kwargs
            assert call_kwargs["tavily_api_key"] == "test-tavily-key"
    
    def test_get_tavily_tool_missing_api_key(self, monkeypatch):
        """Test Tavily tool initialization with missing API key."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            get_tavily_tool()
    
    def test_get_tavily_tool_with_max_results(self, mock_env_vars):
        """Test Tavily tool initialization with max_results parameter."""
        with patch('research_assistant.tools.tavily.TavilySearchResults') as mock_tavily:
            mock_instance = Mock()
            mock_tavily.return_value = mock_instance
            
            tool = get_tavily_tool()
            
            # Verify max_results is set
            call_kwargs = mock_tavily.call_args[1]
            assert call_kwargs.get("max_results") == 5


@pytest.mark.unit
class TestTavilyToolUsage:
    """Test Tavily tool usage."""
    
    def test_tavily_tool_has_correct_attributes(self, mock_env_vars):
        """Test that Tavily tool has correct attributes."""
        with patch('research_assistant.tools.tavily.TavilySearchResults') as mock_tavily:
            mock_instance = Mock()
            mock_instance.name = "tavily_search_results_json"
            mock_instance.description = "A search engine"
            mock_tavily.return_value = mock_instance
            
            tool = get_tavily_tool()
            
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "invoke")

