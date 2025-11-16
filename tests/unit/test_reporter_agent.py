"""Unit tests for ReporterAgent class."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.agents.reporter import ReporterAgent
from langchain_openai import ChatOpenAI


@pytest.mark.unit
class TestReporterAgentInitialization:
    """Test ReporterAgent initialization."""
    
    def test_initialization_with_default_llm(self, mock_llm):
        """Test ReporterAgent initialization with default LLM."""
        with patch('research_assistant.agents.reporter.ChatOpenAI', return_value=mock_llm):
            agent = ReporterAgent()
            
            assert agent.llm is not None
            assert len(agent.tools) == 0
    
    def test_initialization_with_custom_llm(self, mock_llm):
        """Test ReporterAgent initialization with custom LLM."""
        agent = ReporterAgent(llm=mock_llm)
        
        assert agent.llm == mock_llm
        assert len(agent.tools) == 0


@pytest.mark.unit
class TestSynthesizeMethod:
    """Test synthesis method execution."""
    
    def test_synthesize_with_research_findings_only(self, mock_llm):
        """Test synthesis with only research findings."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "Based on the research findings, transformers are neural network architectures..."
        mock_llm.invoke.return_value = mock_response
        
        research_findings = {
            "result": "Transformers use attention mechanisms for sequence processing.",
            "traces": []
        }
        
        result = agent.synthesize(
            question="What are transformers?",
            research_findings=research_findings,
            coder_results=None
        )
        
        assert "result" in result
        assert "traces" in result
        assert "final_act" in result
        assert result["final_act"] == "synthesize"
        assert len(result["traces"]) == 1
    
    def test_synthesize_with_coder_results_only(self, mock_llm):
        """Test synthesis with only coder results."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "The code execution shows that fibonacci(10) equals 55."
        mock_llm.invoke.return_value = mock_response
        
        coder_results = {
            "result": "Code executed. fibonacci(10) = 55",
            "traces": []
        }
        
        result = agent.synthesize(
            question="Calculate fibonacci(10)",
            research_findings=None,
            coder_results=coder_results
        )
        
        assert result["result"] is not None
        assert "fibonacci" in result["result"].lower() or "55" in result["result"]
    
    def test_synthesize_with_both_results(self, mock_llm):
        """Test synthesis with both research and code results."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "Research shows transformers use attention. Code validates the calculation."
        mock_llm.invoke.return_value = mock_response
        
        research_findings = {
            "result": "Transformers are neural networks with attention mechanisms.",
            "traces": []
        }
        
        coder_results = {
            "result": "Attention calculation validated: output shape (3, 4)",
            "traces": []
        }
        
        result = agent.synthesize(
            question="Research transformers and validate attention mechanism",
            research_findings=research_findings,
            coder_results=coder_results
        )
        
        assert result["result"] is not None
        assert len(result["traces"]) == 1
    
    def test_synthesize_with_no_results(self, mock_llm):
        """Test synthesis with no results."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "I don't have sufficient information to answer this question."
        mock_llm.invoke.return_value = mock_response
        
        result = agent.synthesize(
            question="What is machine learning?",
            research_findings=None,
            coder_results=None
        )
        
        assert result["result"] is not None
        assert "No research findings available" in str(mock_llm.invoke.call_args) or result["result"] is not None
    
    def test_synthesize_trace_generation(self, mock_llm):
        """Test that synthesis generates proper traces."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "Synthesized response"
        mock_llm.invoke.return_value = mock_response
        
        result = agent.synthesize(
            question="Test question",
            research_findings={"result": "Test findings"},
            coder_results=None
        )
        
        assert "traces" in result
        assert len(result["traces"]) == 1
        trace = result["traces"][0]
        assert "iteration" in trace
        assert "thought" in trace
        assert "act" in trace
        assert "observation" in trace
    
    def test_synthesize_with_empty_research_result(self, mock_llm):
        """Test synthesis with empty research result."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "Response without research findings"
        mock_llm.invoke.return_value = mock_response
        
        research_findings = {"result": ""}
        
        result = agent.synthesize(
            question="Test question",
            research_findings=research_findings,
            coder_results=None
        )
        
        assert result["result"] is not None
    
    def test_synthesize_with_empty_coder_result(self, mock_llm):
        """Test synthesis with empty coder result."""
        agent = ReporterAgent(llm=mock_llm)
        
        mock_response = Mock()
        mock_response.content = "Response without code results"
        mock_llm.invoke.return_value = mock_response
        
        coder_results = {"result": ""}
        
        result = agent.synthesize(
            question="Test question",
            research_findings=None,
            coder_results=coder_results
        )
        
        assert result["result"] is not None

