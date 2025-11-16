"""Unit tests for PlannerAgent class."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.agents.planner import PlannerAgent, RoutingDecision
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage


@pytest.mark.unit
class TestPlannerAgentInitialization:
    """Test PlannerAgent initialization."""
    
    def test_initialization_with_default_llm(self, mock_llm):
        """Test PlannerAgent initialization with default LLM."""
        with patch('research_assistant.agents.planner.ChatOpenAI', return_value=mock_llm):
            agent = PlannerAgent()
            
            assert agent.llm is not None
            assert len(agent.tools) == 0
    
    def test_initialization_with_custom_llm(self, mock_llm):
        """Test PlannerAgent initialization with custom LLM."""
        agent = PlannerAgent(llm=mock_llm)
        
        assert agent.llm == mock_llm
        assert len(agent.tools) == 0


@pytest.mark.unit
class TestDecideNextStepMethod:
    """Test decide_next_step method."""
    
    def test_decide_next_step_with_empty_history(self, mock_llm):
        """Test routing decision with empty conversation history."""
        agent = PlannerAgent(llm=mock_llm)
        
        # Mock structured LLM response
        mock_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research is needed first",
            task_description="Research and validate transformers",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = mock_decision
            
            decision = agent.decide_next_step("Research and validate transformers", [])
            
            assert decision.next_agent == "researcher"
            assert decision.reasoning is not None
            assert decision.task_description is not None
    
    def test_decide_next_step_with_conversation_history(self, mock_llm):
        """Test routing decision with conversation history."""
        agent = PlannerAgent(llm=mock_llm)
        
        # Create conversation history with research results
        history = [
            HumanMessage(content="Research transformers"),
            AIMessage(content="Research Agent Results: Transformers are neural networks...")
        ]
        
        # Mock structured LLM response
        mock_decision = RoutingDecision(
            next_agent="coder",
            reasoning="Research complete, now need code validation",
            task_description="Validate transformers with code",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = mock_decision
            
            decision = agent.decide_next_step("Research and validate transformers", history)
            
            assert decision.next_agent == "coder"
            assert "research" in decision.reasoning.lower() or "code" in decision.reasoning.lower()
    
    def test_decide_next_step_with_empty_question(self, mock_llm):
        """Test routing decision with empty question."""
        agent = PlannerAgent(llm=mock_llm)
        
        decision = agent.decide_next_step("", [])
        
        # Should default to researcher
        assert decision.next_agent == "researcher"
        assert decision.reasoning is not None


@pytest.mark.unit
class TestRoutingLogic:
    """Test routing decision methods."""
    
    def test_should_route_to_research_with_research_keyword(self, mock_llm):
        """Test routing to research agent with research keyword."""
        agent = PlannerAgent(llm=mock_llm)
        
        # Mock routing decisions for research queries
        research_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research needed",
            task_description="Research task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = research_decision
            
            assert agent.should_route_to_research("Research transformer architectures") is True
            assert agent.should_route_to_research("Find information about AI") is True
            assert agent.should_route_to_research("What is machine learning?") is True
            assert agent.should_route_to_research("Search for latest news") is True
    
    def test_should_route_to_research_with_question_words(self, mock_llm):
        """Test routing to research agent with question words."""
        agent = PlannerAgent(llm=mock_llm)
        
        research_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research needed",
            task_description="Research task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = research_decision
            
            assert agent.should_route_to_research("What are transformers?") is True
            assert agent.should_route_to_research("Who invented neural networks?") is True
            assert agent.should_route_to_research("When was GPT-3 released?") is True
            assert agent.should_route_to_research("Where is AI used?") is True
            assert agent.should_route_to_research("How does attention work?") is True
            assert agent.should_route_to_research("Why use transformers?") is True
    
    def test_should_route_to_research_negative_cases(self, mock_llm):
        """Test routing to research agent with negative cases."""
        agent = PlannerAgent(llm=mock_llm)
        
        # Mock non-research decisions
        coder_decision = RoutingDecision(
            next_agent="coder",
            reasoning="Code needed",
            task_description="Code task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = coder_decision
            
            # Empty string defaults to researcher in decide_next_step
            empty_decision = RoutingDecision(
                next_agent="researcher",
                reasoning="Default",
                task_description="Analyze",
                is_complete=False
            )
            mock_structured.invoke.side_effect = [empty_decision, coder_decision, coder_decision]
            
            # Empty string will default to researcher
            result1 = agent.should_route_to_research("")
            assert result1 is True  # Empty defaults to researcher
            
            assert agent.should_route_to_research("Calculate fibonacci") is False
            assert agent.should_route_to_research("Execute code") is False
    
    def test_should_route_to_coder_with_code_keyword(self, mock_llm):
        """Test routing to coder agent with code keyword."""
        agent = PlannerAgent(llm=mock_llm)
        
        coder_decision = RoutingDecision(
            next_agent="coder",
            reasoning="Code needed",
            task_description="Code task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = coder_decision
            
            assert agent.should_route_to_coder("Code a fibonacci function") is True
            assert agent.should_route_to_coder("Validate the algorithm") is True
            assert agent.should_route_to_coder("Calculate the result") is True
            assert agent.should_route_to_coder("Execute this script") is True
    
    def test_should_route_to_coder_negative_cases(self, mock_llm):
        """Test routing to coder agent with negative cases."""
        agent = PlannerAgent(llm=mock_llm)
        
        research_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research needed",
            task_description="Research task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.return_value = research_decision
            
            # Empty string defaults to researcher
            empty_decision = RoutingDecision(
                next_agent="researcher",
                reasoning="Default",
                task_description="Analyze",
                is_complete=False
            )
            mock_structured.invoke.side_effect = [empty_decision, research_decision, research_decision]
            
            result1 = agent.should_route_to_coder("")
            assert result1 is False  # Empty defaults to researcher
            
            assert agent.should_route_to_coder("Research transformers") is False
            assert agent.should_route_to_coder("Find information") is False
    
    def test_should_route_to_coder_case_insensitive(self, mock_llm):
        """Test routing is case insensitive."""
        agent = PlannerAgent(llm=mock_llm)
        
        coder_decision = RoutingDecision(
            next_agent="coder",
            reasoning="Code needed",
            task_description="Code task",
            is_complete=False
        )
        research_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research needed",
            task_description="Research task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.side_effect = [coder_decision, coder_decision, research_decision, research_decision]
            
            assert agent.should_route_to_coder("CODE fibonacci") is True
            assert agent.should_route_to_coder("Validate Algorithm") is True
            assert agent.should_route_to_research("RESEARCH transformers") is True
            assert agent.should_route_to_research("Find Information") is True
    
    def test_routing_with_combined_keywords(self, mock_llm):
        """Test routing with queries containing multiple keywords."""
        agent = PlannerAgent(llm=mock_llm)
        
        # For combined queries, the LLM decides based on context
        research_decision = RoutingDecision(
            next_agent="researcher",
            reasoning="Research first",
            task_description="Research task",
            is_complete=False
        )
        coder_decision = RoutingDecision(
            next_agent="coder",
            reasoning="Code needed",
            task_description="Code task",
            is_complete=False
        )
        
        with patch.object(agent, 'structured_llm') as mock_structured:
            mock_structured.invoke.side_effect = [research_decision, coder_decision]
            
            # Should route to research if research keyword present
            assert agent.should_route_to_research("Research and code transformers") is True
            # Should route to coder if code keyword present
            assert agent.should_route_to_coder("Research and code transformers") is True

