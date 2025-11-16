"""Unit tests for CoderAgent class."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.agents.coder import CoderAgent
from langchain_openai import ChatOpenAI


@pytest.mark.unit
class TestCoderAgentInitialization:
    """Test CoderAgent initialization."""
    
    def test_initialization_with_default_llm(self, mock_llm, mock_python_repl_tool):
        """Test CoderAgent initialization with default LLM."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            with patch('research_assistant.agents.coder.ChatOpenAI', return_value=mock_llm):
                agent = CoderAgent()
                
                assert agent.llm is not None
                assert len(agent.tools) == 1
                assert mock_python_repl_tool.name in agent.tool_map
    
    def test_initialization_with_custom_llm(self, mock_llm, mock_python_repl_tool):
        """Test CoderAgent initialization with custom LLM."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            agent = CoderAgent(llm=mock_llm)
            
            assert agent.llm == mock_llm
            assert len(agent.tools) == 1
            assert agent.tools[0] == mock_python_repl_tool


@pytest.mark.unit
class TestCodeMethod:
    """Test code execution method."""
    
    def test_code_with_task(self, mock_llm, mock_python_repl_tool):
        """Test code method with task."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            agent = CoderAgent(llm=mock_llm)
            
            mock_response = Mock()
            mock_response.content = """Thought: Code executed successfully.
Action: finish"""
            mock_llm.invoke.return_value = mock_response
            
            result = agent.code(task="Calculate fibonacci(10)")
            
            assert "result" in result
            assert "traces" in result
            assert "final_act" in result
    
    def test_code_with_previous_code(self, mock_llm, mock_python_repl_tool):
        """Test code method with previous code context."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            agent = CoderAgent(llm=mock_llm)
            
            mock_response = Mock()
            mock_response.content = """Thought: Task complete.
Action: finish"""
            mock_llm.invoke.return_value = mock_response
            
            previous_code = "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)"
            result = agent.code(
                task="Calculate fib(10)",
                previous_code=previous_code
            )
            
            assert result is not None
            assert "result" in result
    
    def test_code_with_empty_previous_code(self, mock_llm, mock_python_repl_tool):
        """Test code method with empty previous code."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            agent = CoderAgent(llm=mock_llm)
            
            mock_response = Mock()
            mock_response.content = """Thought: Task complete.
Action: finish"""
            mock_llm.invoke.return_value = mock_response
            
            result = agent.code(
                task="Calculate 2+2",
                previous_code=None
            )
            
            assert result is not None
    
    def test_code_tool_integration(self, mock_llm, mock_python_repl_tool):
        """Test code method integrates with Python REPL tool."""
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
            
            # Verify tool was called or result is valid
            assert result is not None

