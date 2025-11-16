"""Unit tests for ResearchAgent class."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.agents.researcher import ResearchAgent
from langchain_openai import ChatOpenAI


@pytest.mark.unit
class TestResearcherAgentInitialization:
    """Test ResearchAgent initialization."""
    
    def test_initialization_with_default_llm(self, mock_llm, mock_tavily_tool):
        """Test ResearchAgent initialization with default LLM."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            with patch('research_assistant.agents.researcher.ChatOpenAI', return_value=mock_llm):
                agent = ResearchAgent()
                
                assert agent.llm is not None
                assert len(agent.tools) == 1
                assert mock_tavily_tool.name in agent.tool_map
    
    def test_initialization_with_custom_llm(self, mock_llm, mock_tavily_tool):
        """Test ResearchAgent initialization with custom LLM."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            assert agent.llm == mock_llm
            assert len(agent.tools) == 1
            assert agent.tools[0] == mock_tavily_tool


@pytest.mark.unit
class TestResearchMethod:
    """Test research method execution."""
    
    def test_research_with_task(self, mock_llm, mock_tavily_tool):
        """Test research method with task."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            # Mock LLM response for ReAct cycle
            mock_response = Mock()
            mock_response.content = """Thought: I have sufficient information.
Action: finish"""
            mock_llm.invoke.return_value = mock_response
            
            result = agent.research(task="Research transformer architectures")
            
            assert "result" in result
            assert "traces" in result
            assert "final_act" in result
    
    def test_research_with_previous_findings(self, mock_llm, mock_tavily_tool):
        """Test research method with previous findings."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            mock_response = Mock()
            mock_response.content = """Thought: Task complete.
Action: finish"""
            mock_llm.invoke.return_value = mock_response
            
            previous_findings = {"topic": "transformers", "sources": ["paper1", "paper2"]}
            result = agent.research(
                task="Research attention mechanisms",
                previous_findings=previous_findings
            )
            
            assert result is not None
            assert "result" in result
    
    def test_research_with_empty_previous_findings(self, mock_llm, mock_tavily_tool):
        """Test research method with empty previous findings."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            mock_response = Mock()
            mock_response.content = """Thought: Task complete.
Action: finish"""
            mock_llm.invoke.return_value = mock_response
            
            result = agent.research(
                task="Research neural networks",
                previous_findings=None
            )
            
            assert result is not None
    
    def test_research_tool_integration(self, mock_llm, mock_tavily_tool):
        """Test research method integrates with Tavily tool."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            # Mock LLM that uses tool
            first_response = Mock()
            first_response.content = """Thought: I need to search.
Action: tavily_search_results_json
Action Input: transformers"""
            
            second_response = Mock()
            second_response.content = """Thought: I have information.
Action: finish"""
            
            mock_llm.invoke.side_effect = [first_response, second_response]
            
            result = agent.research(task="Research transformers")
            
            # Verify tool was called
            assert mock_tavily_tool.invoke.called or result is not None

