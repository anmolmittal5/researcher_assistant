"""Reporter agent for synthesizing final responses from research and code results."""

from typing import Dict, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from research_assistant.agents.base import BaseReActAgent
from research_assistant.prompts.reporter import REPORTER_PROMPT


class ReporterAgent(BaseReActAgent):
    """Agent that synthesizes final responses from Research and Coder agent outputs."""

    def __init__(self, llm: ChatOpenAI = None):
        """Initialize Reporter agent with LLM."""
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        super().__init__(
            llm=llm,
            system_prompt=REPORTER_PROMPT,
            tools=[],
        )

    def synthesize(
        self,
        question: str,
        research_findings: Dict[str, Any] = None,
        coder_results: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Synthesize final response from research and code results."""
        research_content = ""
        if research_findings:
            research_content = research_findings.get("result", "")
        
        coder_content = ""
        if coder_results:
            coder_content = coder_results.get("result", "")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_system_prompt = self.system_prompt.format(
            question=question,
            research_findings=research_content if research_content else "No research findings available.",
            coder_results=coder_content if coder_content else "No code execution results available.",
            time=current_time
        )
        
        synthesis_prompt = f"""{formatted_system_prompt}

Synthesize a clear, comprehensive final response that directly answers the user's question. 
Use the research findings and code results to provide a well-structured answer."""

        response = self.llm.invoke(synthesis_prompt)
        synthesized_text = response.content
        
        return {
            "result": synthesized_text,
            "traces": [{
                "iteration": 1,
                "thought": f"Synthesizing final response from research and code results for question: {question[:100]}...",
                "act": "synthesize",
                "observation": f"Generated comprehensive response of {len(synthesized_text)} characters",
            }],
            "final_act": "synthesize",
        }

