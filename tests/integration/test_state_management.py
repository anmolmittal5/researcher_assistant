"""Integration tests for state management."""

import pytest
from research_assistant.graph.state import AgentState


@pytest.mark.integration
class TestAgentState:
    """Test AgentState structure and usage."""
    
    def test_agent_state_structure(self):
        """Test that AgentState has correct structure."""
        state: AgentState = {
            "goal": "Test goal",
            "messages": [],
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
        
        assert state["goal"] == "Test goal"
        assert isinstance(state["messages"], list)
        assert isinstance(state["tasks"], list)
        assert isinstance(state["results"], list)
        assert isinstance(state["traces"], list)
    
    def test_agent_state_with_results(self):
        """Test AgentState with populated results."""
        state: AgentState = {
            "goal": "Research and code",
            "messages": [],
            "tasks": ["research", "code"],
            "current_task": "research",
            "research_results": {
                "result": "Research findings",
                "traces": []
            },
            "coder_results": None,
            "planner_results": {
                "decision": "researcher",
                "reasoning": "Route to researcher"
            },
            "reporter_results": None,
            "routing_decision": {
                "next_agent": "researcher",
                "reasoning": "Route to researcher",
                "task_description": "Research transformers"
            },
            "results": [],
            "traces": [],
        }
        
        assert state["planner_results"] is not None
        assert len(state["tasks"]) == 2
        assert state["research_results"] is not None
        assert state["coder_results"] is None
        assert state["routing_decision"] is not None
    
    def test_agent_state_updates(self):
        """Test updating AgentState fields."""
        from langchain_core.messages import HumanMessage
        
        state: AgentState = {
            "goal": "Initial goal",
            "messages": [],
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
        
        # Update state
        state["messages"] = [HumanMessage(content="Test message")]
        state["tasks"] = ["task1", "task2"]
        state["current_task"] = "task1"
        state["routing_decision"] = {
            "next_agent": "researcher",
            "reasoning": "Need to research",
            "task_description": "task1"
        }
        
        assert len(state["messages"]) == 1
        assert len(state["tasks"]) == 2
        assert state["current_task"] == "task1"
        assert state["routing_decision"]["next_agent"] == "researcher"

