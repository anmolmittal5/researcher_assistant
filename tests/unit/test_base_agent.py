"""Unit tests for BaseReActAgent class."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from research_assistant.agents.base import BaseReActAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


@pytest.mark.unit
class TestBaseAgentInitialization:
    """Test BaseReActAgent initialization."""
    
    def test_initialization_with_llm_and_prompt(self, mock_llm, sample_system_prompt):
        """Test agent initialization with LLM and system prompt."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        assert agent.llm == mock_llm
        assert agent.system_prompt == sample_system_prompt
        assert agent.tools == []
        assert agent.max_iterations == 5
        assert agent.traces == []
        assert agent.tool_map == {}
    
    def test_initialization_with_tools(self, mock_llm, sample_system_prompt, mock_tavily_tool):
        """Test agent initialization with tools."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[mock_tavily_tool]
        )
        
        assert len(agent.tools) == 1
        assert mock_tavily_tool.name in agent.tool_map
        assert agent.tool_map[mock_tavily_tool.name] == mock_tavily_tool
    
    def test_initialization_with_custom_max_iterations(self, mock_llm, sample_system_prompt):
        """Test agent initialization with custom max iterations."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[],
            max_iterations=10
        )
        
        assert agent.max_iterations == 10


@pytest.mark.unit
class TestToolExecution:
    """Test tool execution functionality."""
    
    def test_execute_tool_success(self, mock_llm, sample_system_prompt, mock_tavily_tool):
        """Test successful tool execution."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[mock_tavily_tool]
        )
        
        result = agent._execute_tool("tavily_search_results_json", "test query")
        
        assert result is not None
        mock_tavily_tool.invoke.assert_called_once_with("test query")
    
    def test_execute_tool_not_found(self, mock_llm, sample_system_prompt):
        """Test tool not found error handling."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        result = agent._execute_tool("nonexistent_tool", "input")
        
        assert "not found" in result.lower()
        assert "available tools" in result.lower()
    
    def test_execute_tool_with_string_result(self, mock_llm, sample_system_prompt, mock_python_repl_tool):
        """Test tool execution returning string result."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[mock_python_repl_tool]
        )
        
        result = agent._execute_tool("python_repl", "print('hello')")
        
        assert isinstance(result, str)
        assert "Code executed successfully" in result
    
    def test_execute_tool_with_list_result(self, mock_llm, sample_system_prompt, mock_tavily_tool):
        """Test tool execution returning list result."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[mock_tavily_tool]
        )
        
        result = agent._execute_tool("tavily_search_results_json", "test")
        
        assert isinstance(result, str)
        assert "Test Result 1" in result
        assert "Test Result 2" in result
    
    def test_execute_tool_error_handling(self, mock_llm, sample_system_prompt):
        """Test tool execution error handling."""
        error_tool = Mock()
        error_tool.name = "error_tool"
        error_tool.invoke.side_effect = Exception("Tool execution failed")
        
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[error_tool]
        )
        
        result = agent._execute_tool("error_tool", "input")
        
        assert "Error executing" in result
        assert "error_tool" in result


@pytest.mark.unit
class TestResponseParsing:
    """Test response parsing functionality."""
    
    def test_parse_standard_response(self, mock_llm, sample_system_prompt):
        """Test parsing standard ReAct format response."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        response = """Thought: I need to search for information.
Action: tavily_search
Action Input: test query"""
        
        thought, action, action_input = agent._parse_response(response)
        
        assert "search for information" in thought.lower()
        assert action == "tavily_search"
        assert action_input == "test query"
    
    def test_parse_response_with_action_input_separate(self, mock_llm, sample_system_prompt):
        """Test parsing response with Action Input on separate line."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        response = """Thought: I need to execute code.
Action: python_repl
Action Input: print('hello')"""
        
        thought, action, action_input = agent._parse_response(response)
        
        assert "execute code" in thought.lower()
        assert action == "python_repl"
        assert action_input == "print('hello')"
    
    def test_parse_response_with_multiline_thought(self, mock_llm, sample_system_prompt):
        """Test parsing response with multiline thought."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        response = """Thought: This is a complex thought
that spans multiple lines
and needs proper parsing.
Action: finish"""
        
        thought, action, action_input = agent._parse_response(response)
        
        assert "complex thought" in thought.lower()
        assert "spans multiple lines" in thought.lower()
        assert action == "finish"
    
    def test_parse_response_missing_fields(self, mock_llm, sample_system_prompt):
        """Test parsing response with missing fields."""
        agent = BaseReActAgent(
            llm=mock_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        response = "Just some text without proper format"
        
        thought, action, action_input = agent._parse_response(response)
        
        assert thought == ""
        assert action == ""
        assert action_input == ""


@pytest.mark.unit
class TestReActLoop:
    """Test ReAct loop execution."""
    
    def test_react_loop_complete_cycle(self, mock_llm_with_react_cycle, sample_system_prompt, mock_tavily_tool):
        """Test complete ReAct cycle execution."""
        agent = BaseReActAgent(
            llm=mock_llm_with_react_cycle,
            system_prompt=sample_system_prompt,
            tools=[mock_tavily_tool],
            max_iterations=5
        )
        
        result = agent.run(task="Test task")
        
        assert "result" in result
        assert "traces" in result
        assert len(result["traces"]) > 0
        assert result["final_act"] == "finish"
    
    def test_react_loop_with_observations(self, mock_llm_with_react_cycle, sample_system_prompt, mock_tavily_tool):
        """Test ReAct loop with observation handling."""
        agent = BaseReActAgent(
            llm=mock_llm_with_react_cycle,
            system_prompt=sample_system_prompt,
            tools=[mock_tavily_tool],
            max_iterations=5
        )
        
        result = agent.run(task="Test task")
        
        # Check that observations are stored in traces
        traces = result["traces"]
        assert len(traces) > 0
        # First trace should have observation if tool was called
        if traces[0].get("observation"):
            assert len(traces[0]["observation"]) > 0
    
    def test_react_loop_max_iterations(self, mock_llm, sample_system_prompt):
        """Test ReAct loop hitting max iterations limit."""
        # Mock LLM that never finishes
        never_finish_llm = Mock(spec=ChatOpenAI)
        never_finish_response = Mock()
        never_finish_response.content = """Thought: Still working.
Action: continue_work
Action Input: more work"""
        never_finish_llm.invoke.return_value = never_finish_response
        
        agent = BaseReActAgent(
            llm=never_finish_llm,
            system_prompt=sample_system_prompt,
            tools=[],
            max_iterations=2
        )
        
        result = agent.run(task="Test task")
        
        assert result["final_act"] == "max_iterations"
        assert len(result["traces"]) == 2
    
    def test_react_loop_early_finish(self, mock_llm, sample_system_prompt):
        """Test ReAct loop with early finish."""
        finish_llm = Mock(spec=ChatOpenAI)
        finish_response = Mock()
        finish_response.content = """Thought: Task is complete.
Action: finish"""
        finish_llm.invoke.return_value = finish_response
        
        agent = BaseReActAgent(
            llm=finish_llm,
            system_prompt=sample_system_prompt,
            tools=[],
            max_iterations=5
        )
        
        result = agent.run(task="Test task")
        
        assert result["final_act"] == "finish"
        assert len(result["traces"]) == 1
    
    def test_react_loop_context_handling(self, mock_llm, sample_system_prompt):
        """Test ReAct loop with context."""
        finish_llm = Mock(spec=ChatOpenAI)
        finish_response = Mock()
        finish_response.content = """Thought: Task is complete.
Action: finish"""
        finish_llm.invoke.return_value = finish_response
        
        agent = BaseReActAgent(
            llm=finish_llm,
            system_prompt=sample_system_prompt,
            tools=[]
        )
        
        context = {"previous_findings": {"key": "value"}}
        result = agent.run(task="Test task", context=context)
        
        assert result["final_act"] == "finish"
        # Verify context was passed to LLM
        assert finish_llm.invoke.called

