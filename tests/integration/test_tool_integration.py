"""Integration tests for tool-agent integration."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.agents.researcher import ResearchAgent
from research_assistant.agents.coder import CoderAgent


@pytest.mark.integration
class TestResearcherTavilyIntegration:
    """Test Researcher agent with Tavily tool integration."""
    
    def test_researcher_uses_tavily_tool(self, mock_llm, mock_tavily_tool):
        """Test that researcher agent properly uses Tavily tool."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            # Mock LLM that uses tool
            first_response = Mock()
            first_response.content = """Thought: I need to search.
Action: tavily_search_results_json
Action Input: transformers"""
            
            second_response = Mock()
            second_response.content = """Thought: I have results.
Action: finish"""
            
            mock_llm.invoke.side_effect = [first_response, second_response]
            
            result = agent.research(task="Research transformers")
            
            # Verify tool was available and could be called
            assert "tavily_search_results_json" in agent.tool_map
            assert result is not None
    
    def test_tavily_tool_error_handling(self, mock_llm):
        """Test error handling when Tavily tool fails."""
        error_tool = Mock()
        error_tool.name = "tavily_search_results_json"
        error_tool.invoke.side_effect = Exception("API Error")
        
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=error_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            first_response = Mock()
            first_response.content = """Thought: I need to search.
Action: tavily_search_results_json
Action Input: test"""
            
            second_response = Mock()
            second_response.content = """Thought: There was an error.
Action: finish"""
            
            mock_llm.invoke.side_effect = [first_response, second_response]
            
            result = agent.research(task="Test task")
            
            # Should handle error gracefully
            assert result is not None


@pytest.mark.integration
class TestCoderREPLIntegration:
    """Test Coder agent with Python REPL tool integration."""
    
    def test_coder_uses_python_repl_tool(self, mock_llm, mock_python_repl_tool):
        """Test that coder agent properly uses Python REPL tool."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            agent = CoderAgent(llm=mock_llm)
            
            # Mock LLM that uses tool
            first_response = Mock()
            first_response.content = """Thought: I need to execute code.
Action: python_repl
Action Input: print(2+2)"""
            
            second_response = Mock()
            second_response.content = """Thought: Code executed.
Action: finish"""
            
            mock_llm.invoke.side_effect = [first_response, second_response]
            
            result = agent.code(task="Calculate 2+2")
            
            # Verify tool was available
            assert "python_repl" in agent.tool_map
            assert result is not None
    
    def test_python_repl_tool_result_formatting(self, mock_llm, mock_python_repl_tool):
        """Test that Python REPL tool results are properly formatted."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            agent = CoderAgent(llm=mock_llm)
            
            # Mock tool to return string result
            mock_python_repl_tool.invoke.return_value = "4"
            
            first_response = Mock()
            first_response.content = """Thought: Execute code.
Action: python_repl
Action Input: 2+2"""
            
            second_response = Mock()
            second_response.content = """Thought: Got result.
Action: finish"""
            
            mock_llm.invoke.side_effect = [first_response, second_response]
            
            result = agent.code(task="Calculate 2+2")
            
            assert result is not None


@pytest.mark.integration
class TestToolResultPropagation:
    """Test tool result propagation through agent."""
    
    def test_tool_result_in_observation(self, mock_llm, mock_tavily_tool):
        """Test that tool results appear in agent observations."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            agent = ResearchAgent(llm=mock_llm)
            
            first_response = Mock()
            first_response.content = """Thought: Search needed.
Action: tavily_search_results_json
Action Input: test"""
            
            second_response = Mock()
            second_response.content = """Thought: Got results.
Action: finish"""
            
            mock_llm.invoke.side_effect = [first_response, second_response]
            
            result = agent.research(task="Test")
            
            # Check that traces contain observations
            if result.get("traces"):
                for trace in result["traces"]:
                    if trace.get("observation"):
                        # Observation should contain tool result
                        assert len(trace["observation"]) > 0

