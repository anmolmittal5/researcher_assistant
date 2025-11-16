"""Shared fixtures and mocks for testing."""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage


@pytest.fixture
def mock_llm():
    """Mock ChatOpenAI LLM for testing."""
    llm = Mock(spec=ChatOpenAI)
    llm.model = "gpt-4o"
    llm.temperature = 0
    
    # Default response
    default_response = Mock()
    default_response.content = """Thought: I need to analyze this task.
Action: finish
Action Input: Task completed successfully."""
    llm.invoke.return_value = default_response
    
    return llm


@pytest.fixture
def mock_llm_with_react_cycle():
    """Mock LLM that returns a complete ReAct cycle."""
    llm = Mock(spec=ChatOpenAI)
    
    # First call: Thought and Action
    first_response = Mock()
    first_response.content = """Thought: I need to search for information about this topic.
Action: tavily_search
Action Input: test query"""
    
    # Second call: Finish after observation
    second_response = Mock()
    second_response.content = """Thought: I have gathered sufficient information.
Action: finish"""
    
    llm.invoke.side_effect = [first_response, second_response]
    return llm


@pytest.fixture
def mock_tavily_tool():
    """Mock Tavily search tool."""
    tool = Mock()
    tool.name = "tavily_search_results_json"
    tool.description = "A search engine. Useful for when you need to answer questions about current events."
    
    # Mock search results
    mock_results = [
        {
            "title": "Test Result 1",
            "url": "https://example.com/1",
            "content": "This is test content from result 1."
        },
        {
            "title": "Test Result 2",
            "url": "https://example.com/2",
            "content": "This is test content from result 2."
        }
    ]
    tool.invoke.return_value = mock_results
    return tool


@pytest.fixture
def mock_python_repl_tool():
    """Mock Python REPL tool."""
    tool = Mock()
    tool.name = "python_repl"
    tool.description = "A Python shell. Use this to execute python commands."
    
    # Mock code execution result
    tool.invoke.return_value = "Code executed successfully. Output: 42"
    return tool


@pytest.fixture
def sample_system_prompt():
    """Sample system prompt for testing."""
    return """You are a helpful assistant.
Follow the ReAct pattern: Thought → Act → Observation
Current date and time: {time}"""


@pytest.fixture
def sample_research_response():
    """Sample LLM response for research agent."""
    return """Thought: I need to search for information about transformers.
Action: tavily_search_results_json
Action Input: transformer architectures neural networks

Observation: Found information about transformers...

Thought: I have sufficient information.
Action: finish"""


@pytest.fixture
def sample_coder_response():
    """Sample LLM response for coder agent."""
    return """Thought: I need to write code to calculate fibonacci numbers.
Action: python_repl
Action Input: def fib(n): return n if n < 2 else fib(n-1) + fib(n-2); print(fib(10))

Observation: Code executed. Output: 55

Thought: Code executed successfully.
Action: finish"""




@pytest.fixture
def sample_trace():
    """Sample trace structure."""
    return {
        "iteration": 1,
        "thought": "I need to search for information",
        "act": "tavily_search_results_json: test query",
        "observation": "Found 2 results about the topic",
    }


@pytest.fixture
def sample_research_result():
    """Sample research agent result."""
    return {
        "result": "Transformers are neural network architectures that use attention mechanisms...",
        "traces": [
            {
                "iteration": 1,
                "thought": "I need to search for information about transformers",
                "act": "tavily_search_results_json: transformer architectures",
                "observation": "Found multiple results about transformers",
            }
        ],
        "final_act": "finish",
    }


@pytest.fixture
def sample_coder_result():
    """Sample coder agent result."""
    return {
        "result": "Code executed successfully. Fibonacci(10) = 55",
        "traces": [
            {
                "iteration": 1,
                "thought": "I need to write code to calculate fibonacci",
                "act": "python_repl: def fib(n): ...",
                "observation": "Code executed. Output: 55",
            }
        ],
        "final_act": "finish",
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")


@pytest.fixture
def research_keywords():
    """List of research-related keywords for testing."""
    return [
        "research", "search", "find", "information", "document",
        "news", "latest", "recent", "what", "who", "when", "where",
        "how", "why", "ai", "artificial intelligence"
    ]


@pytest.fixture
def coder_keywords():
    """List of coder-related keywords for testing."""
    return ["code", "validate", "calculate", "execute", "script"]


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return {
        "research": "What are the latest developments in transformer architectures?",
        "coder": "Calculate the first 10 Fibonacci numbers",
        "combined": "Research gradient descent and validate with code",
        "simple": "What is machine learning?",
    }


@pytest.fixture
def mock_workflow(mock_llm):
    """Mock workflow for testing."""
    from unittest.mock import Mock, patch
    from research_assistant.graph.workflow import create_workflow
    
    with patch('research_assistant.graph.workflow.ChatOpenAI', return_value=mock_llm):
        workflow = create_workflow(llm=mock_llm)
        return workflow


@pytest.fixture
def sample_agent_state():
    """Sample AgentState for workflow testing with correct structure."""
    from langchain_core.messages import HumanMessage
    from research_assistant.graph.state import AgentState
    
    return {
        "goal": "Test goal",
        "messages": [HumanMessage(content="Test goal")],
        "tasks": [],
        "current_task": None,
        "research_results": None,
        "coder_results": None,
        "planner_results": None,
        "reporter_results": None,
        "routing_decision": None,
        "results": [],
        "traces": [],
    }


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    yield
    # Cleanup if needed
    pass

