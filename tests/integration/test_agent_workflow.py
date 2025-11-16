"""Integration tests for multi-agent workflows."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.agents.planner import PlannerAgent
from research_assistant.agents.researcher import ResearchAgent
from research_assistant.agents.coder import CoderAgent
from research_assistant.agents.reporter import ReporterAgent


@pytest.mark.integration
class TestPlannerResearcherWorkflow:
    """Test Planner → Researcher workflow."""
    
    def test_planner_to_researcher_flow(self, mock_llm, mock_tavily_tool):
        """Test complete flow from planner to researcher."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            planner = PlannerAgent(llm=mock_llm)
            researcher = ResearchAgent(llm=mock_llm)
            
            # Mock planner routing decision
            from research_assistant.agents.planner import RoutingDecision
            mock_decision = RoutingDecision(
                next_agent="researcher",
                reasoning="Research is needed",
                task_description="Research transformers",
                is_complete=False
            )
            
            with patch.object(planner, 'structured_llm') as mock_structured:
                mock_structured.invoke.return_value = mock_decision
                
                decision = planner.decide_next_step("Research transformers", [])
                
                assert decision.next_agent == "researcher"
            
            # Mock researcher response
            research_response = Mock()
            research_response.content = """Thought: I have sufficient information.
Action: finish"""
            mock_llm.invoke.return_value = research_response
            
            research_result = researcher.research(task="Research transformer architectures")
            
            assert research_result is not None
            assert "result" in research_result


@pytest.mark.integration
class TestPlannerCoderWorkflow:
    """Test Planner → Coder workflow."""
    
    def test_planner_to_coder_flow(self, mock_llm, mock_python_repl_tool):
        """Test complete flow from planner to coder."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            planner = PlannerAgent(llm=mock_llm)
            coder = CoderAgent(llm=mock_llm)
            
            # Mock planner routing decision
            from research_assistant.agents.planner import RoutingDecision
            mock_decision = RoutingDecision(
                next_agent="coder",
                reasoning="Code execution is needed",
                task_description="Calculate fibonacci",
                is_complete=False
            )
            
            with patch.object(planner, 'structured_llm') as mock_structured:
                mock_structured.invoke.return_value = mock_decision
                
                decision = planner.decide_next_step("Calculate fibonacci", [])
                
                assert decision.next_agent == "coder"
            
            # Mock coder response
            coder_response = Mock()
            coder_response.content = """Thought: Code executed successfully.
Action: finish"""
            mock_llm.invoke.return_value = coder_response
            
            coder_result = coder.code(task="Calculate fibonacci(10)")
            
            assert coder_result is not None
            assert "result" in coder_result


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete multi-agent workflow."""
    
    def test_research_to_reporter_flow(self, mock_llm, mock_tavily_tool):
        """Test Research → Reporter workflow."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            researcher = ResearchAgent(llm=mock_llm)
            reporter = ReporterAgent(llm=mock_llm)
            
            # Mock researcher response
            research_response = Mock()
            research_response.content = """Thought: I have sufficient information.
Action: finish"""
            mock_llm.invoke.return_value = research_response
            
            research_result = researcher.research(task="Research transformers")
            
            # Mock reporter response
            reporter_response = Mock()
            reporter_response.content = "Based on research, transformers are neural networks..."
            mock_llm.invoke.return_value = reporter_response
            
            reporter_result = reporter.synthesize(
                question="What are transformers?",
                research_findings=research_result,
                coder_results=None
            )
            
            assert reporter_result is not None
            assert reporter_result["final_act"] == "synthesize"
    
    def test_coder_to_reporter_flow(self, mock_llm, mock_python_repl_tool):
        """Test Coder → Reporter workflow."""
        with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
            coder = CoderAgent(llm=mock_llm)
            reporter = ReporterAgent(llm=mock_llm)
            
            # Mock coder response
            coder_response = Mock()
            coder_response.content = """Thought: Code executed successfully.
Action: finish"""
            mock_llm.invoke.return_value = coder_response
            
            coder_result = coder.code(task="Calculate 2+2")
            
            # Mock reporter response
            reporter_response = Mock()
            reporter_response.content = "The code execution shows that 2+2 equals 4."
            mock_llm.invoke.return_value = reporter_response
            
            reporter_result = reporter.synthesize(
                question="Calculate 2+2",
                research_findings=None,
                coder_results=coder_result
            )
            
            assert reporter_result is not None
            assert reporter_result["final_act"] == "synthesize"
    
    def test_full_research_and_code_workflow(self, mock_llm, mock_tavily_tool, mock_python_repl_tool):
        """Test complete workflow: Research → Coder → Reporter."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            with patch('research_assistant.agents.coder.get_python_repl_tool', return_value=mock_python_repl_tool):
                researcher = ResearchAgent(llm=mock_llm)
                coder = CoderAgent(llm=mock_llm)
                reporter = ReporterAgent(llm=mock_llm)
                
                # Research phase
                research_response = Mock()
                research_response.content = """Thought: I have information.
Action: finish"""
                mock_llm.invoke.return_value = research_response
                
                research_result = researcher.research(task="Research attention mechanism")
                
                # Code phase
                coder_response = Mock()
                coder_response.content = """Thought: Code executed.
Action: finish"""
                mock_llm.invoke.return_value = coder_response
                
                coder_result = coder.code(task="Validate attention calculation")
                
                # Reporter phase
                reporter_response = Mock()
                reporter_response.content = "Research shows attention mechanisms. Code validates the calculation."
                mock_llm.invoke.return_value = reporter_response
                
                reporter_result = reporter.synthesize(
                    question="Research attention and validate with code",
                    research_findings=research_result,
                    coder_results=coder_result
                )
                
                assert reporter_result is not None
                assert reporter_result["final_act"] == "synthesize"


@pytest.mark.integration
class TestStateManagement:
    """Test state management across agents."""
    
    def test_state_passing_between_agents(self, mock_llm):
        """Test that state is properly passed between agents."""
        planner = PlannerAgent(llm=mock_llm)
        
        from research_assistant.agents.planner import RoutingDecision
        from langchain_core.messages import HumanMessage
        
        mock_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Test routing",
            task_description="Test goal",
            is_complete=False
        )
        
        with patch.object(planner, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = mock_decision
            
            conversation_history = [HumanMessage(content="Test goal")]
            decision = planner.decide_next_step("Test goal", conversation_history)
            
            # Verify decision was made
            assert decision is not None
            assert decision.next_agent in ["researcher", "coder", "reporter", "finish"]
    
    def test_trace_accumulation(self, mock_llm, mock_tavily_tool):
        """Test that traces accumulate across agent calls."""
        with patch('research_assistant.agents.researcher.get_tavily_tool', return_value=mock_tavily_tool):
            researcher = ResearchAgent(llm=mock_llm)
            
            research_response = Mock()
            research_response.content = """Thought: Task complete.
Action: finish"""
            mock_llm.invoke.return_value = research_response
            
            result = researcher.research(task="Test task")
            
            assert "traces" in result
            assert len(result["traces"]) > 0

