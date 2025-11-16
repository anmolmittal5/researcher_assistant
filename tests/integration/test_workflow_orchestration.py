"""Integration tests for workflow orchestration with loop-based routing."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from research_assistant.graph.workflow import create_workflow
from research_assistant.graph.state import AgentState
from research_assistant.agents.planner import RoutingDecision


@pytest.mark.integration
class TestWorkflowOrchestration:
    """Test LangGraph workflow orchestration with loop-based routing."""
    
    def test_workflow_creation(self, mock_llm):
        """Test that workflow can be created successfully."""
        with patch('research_assistant.graph.workflow.ChatOpenAI', return_value=mock_llm):
            workflow = create_workflow(llm=mock_llm)
            
            assert workflow is not None
            assert hasattr(workflow, 'invoke')
    
    def test_planner_node_routing_decision(self, mock_llm):
        """Test planner node creates routing decision."""
        from research_assistant.graph.workflow import planner_node
        
        # Mock planner agent
        mock_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research is needed",
            task_description="Research transformers",
            is_complete=False
        )
        
        with patch('research_assistant.graph.workflow._planner') as mock_planner:
            mock_planner.decide_next_step.return_value = mock_decision
            
            state: AgentState = {
                "goal": "Research transformers",
                "messages": [HumanMessage(content="Research transformers")],
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
            
            result = planner_node(state)
            
            assert "routing_decision" in result
            assert result["routing_decision"]["next_agent"] == "researcher"
            assert "planner_results" in result
            assert "messages" in result
            assert len(result["messages"]) > len(state["messages"])
    
    def test_research_node_execution(self, mock_llm, mock_tavily_tool):
        """Test research node executes and updates state."""
        from research_assistant.graph.workflow import research_node
        
        with patch('research_assistant.graph.workflow._research') as mock_research:
            mock_research.research.return_value = {
                "result": "Research findings about transformers",
                "traces": [{"iteration": 1, "thought": "Searching", "act": "search", "observation": "Found results"}],
                "final_act": "finish"
            }
            
            state: AgentState = {
                "goal": "Research transformers",
                "messages": [],
                "tasks": [],
                "current_task": "Research transformers",
                "research_results": None,
                "coder_results": None,
                "planner_results": None,
                "reporter_results": None,
                "routing_decision": {
                    "next_agent": "researcher",
                    "task_description": "Research transformers"
                },
                "results": [],
                "traces": [],
            }
            
            result = research_node(state)
            
            assert "research_results" in result
            assert result["research_results"]["result"] is not None
            assert "traces" in result
            assert len(result["traces"]) > 0
            assert "messages" in result
            assert len(result["messages"]) > 0
    
    def test_coder_node_execution(self, mock_llm, mock_python_repl_tool):
        """Test coder node executes and updates state."""
        from research_assistant.graph.workflow import coder_node
        
        with patch('research_assistant.graph.workflow._coder') as mock_coder:
            mock_coder.code.return_value = {
                "result": "Code executed successfully",
                "traces": [{"iteration": 1, "thought": "Coding", "act": "python_repl", "observation": "Executed"}],
                "final_act": "finish"
            }
            
            state: AgentState = {
                "goal": "Calculate fibonacci",
                "messages": [],
                "tasks": [],
                "current_task": "Calculate fibonacci",
                "research_results": None,
                "coder_results": None,
                "planner_results": None,
                "reporter_results": None,
                "routing_decision": {
                    "next_agent": "coder",
                    "task_description": "Calculate fibonacci"
                },
                "results": [],
                "traces": [],
            }
            
            result = coder_node(state)
            
            assert "coder_results" in result
            assert result["coder_results"]["result"] is not None
            assert "traces" in result
            assert len(result["traces"]) > 0
    
    def test_reporter_node_execution(self, mock_llm):
        """Test reporter node synthesizes final response."""
        from research_assistant.graph.workflow import reporter_node
        
        with patch('research_assistant.graph.workflow._reporter') as mock_reporter:
            mock_reporter.synthesize.return_value = {
                "result": "Final synthesized response",
                "traces": [{"iteration": 1, "thought": "Synthesizing", "act": "synthesize", "observation": "Complete"}],
                "final_act": "synthesize"
            }
            
            state: AgentState = {
                "goal": "Research and code",
                "messages": [],
                "tasks": [],
                "current_task": None,
                "research_results": {
                    "result": "Research findings",
                    "traces": []
                },
                "coder_results": {
                    "result": "Code results",
                    "traces": []
                },
                "planner_results": None,
                "reporter_results": None,
                "routing_decision": {
                    "next_agent": "reporter",
                    "task_description": "Synthesize results"
                },
                "results": [],
                "traces": [],
            }
            
            result = reporter_node(state)
            
            assert "reporter_results" in result
            assert result["reporter_results"]["result"] is not None
            assert result.get("is_complete") is True
    
    def test_route_after_planner(self):
        """Test routing function maps planner decisions correctly."""
        from research_assistant.graph.workflow import route_after_planner
        
        # Test researcher routing
        state: AgentState = {
            "routing_decision": {"next_agent": "researcher"},
            "next_agent": "researcher"
        }
        assert route_after_planner(state) == "research"
        
        # Test coder routing
        state = {
            "routing_decision": {"next_agent": "coder"},
            "next_agent": "coder"
        }
        assert route_after_planner(state) == "coder"
        
        # Test reporter routing
        state = {
            "routing_decision": {"next_agent": "reporter"},
            "next_agent": "reporter"
        }
        assert route_after_planner(state) == "reporter"
        
        # Test finish routing
        state = {
            "routing_decision": {"next_agent": "finish"},
            "next_agent": "finish"
        }
        assert route_after_planner(state) == "finish"


@pytest.mark.integration
class TestLoopBasedRouting:
    """Test loop-based routing pattern where agents loop back to planner."""
    
    def test_planner_to_researcher_loop(self, mock_llm):
        """Test planner routes to researcher, then loops back."""
        from research_assistant.graph.workflow import planner_node, research_node
        
        # First planner call
        mock_decision1 = RoutingDecision(
            next_agent="researcher",
            reasoning="Need research",
            task_description="Research transformers",
            is_complete=False
        )
        
        with patch('research_assistant.graph.workflow._planner') as mock_planner:
            mock_planner.decide_next_step.return_value = mock_decision1
            
            state: AgentState = {
                "goal": "Research transformers",
                "messages": [HumanMessage(content="Research transformers")],
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
            
            planner_result = planner_node(state)
            assert planner_result["routing_decision"]["next_agent"] == "researcher"
        
        # Research node execution
        with patch('research_assistant.graph.workflow._research') as mock_research:
            mock_research.research.return_value = {
                "result": "Research complete",
                "traces": [],
                "final_act": "finish"
            }
            
            research_result = research_node(planner_result)
            assert "research_results" in research_result
        
        # Second planner call (after research)
        mock_decision2 = RoutingDecision(
            next_agent="reporter",
            reasoning="Research complete, now synthesize",
            task_description="Synthesize results",
            is_complete=False
        )
        
        with patch('research_assistant.graph.workflow._planner') as mock_planner2:
            mock_planner2.decide_next_step.return_value = mock_decision2
            
            # Planner should see research_results in state
            updated_state = research_result.copy()
            updated_state["messages"] = research_result.get("messages", [])
            
            planner_result2 = planner_node(updated_state)
            # Should route to reporter since research is done
            assert planner_result2["routing_decision"]["next_agent"] == "reporter"
    
    def test_conversation_history_accumulation(self, mock_llm):
        """Test that conversation history accumulates across loop iterations."""
        from research_assistant.graph.workflow import planner_node, research_node
        
        initial_messages = [HumanMessage(content="Research transformers")]
        
        # Planner adds message
        mock_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Need research",
            task_description="Research transformers",
            is_complete=False
        )
        
        with patch('research_assistant.graph.workflow._planner') as mock_planner:
            mock_planner.decide_next_step.return_value = mock_decision
            
            state: AgentState = {
                "goal": "Research transformers",
                "messages": initial_messages,
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
            
            planner_result = planner_node(state)
            assert len(planner_result["messages"]) > len(initial_messages)
        
        # Research adds message
        with patch('research_assistant.graph.workflow._research') as mock_research:
            mock_research.research.return_value = {
                "result": "Research complete",
                "traces": [],
                "final_act": "finish"
            }
            
            research_result = research_node(planner_result)
            assert len(research_result["messages"]) > len(planner_result["messages"])

