"""Research agent for gathering evidence from web sources."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from research_assistant.agents.base import BaseReActAgent
from research_assistant.prompts.research import RESEARCH_PROMPT
from research_assistant.tools import get_tavily_tool


class ResearchAgent(BaseReActAgent):
    """Agent that gathers evidence using Tavily Search."""

    def __init__(self, llm: ChatOpenAI = None):
        """Initialize Research agent with LLM and tools."""
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        tools: List = [get_tavily_tool()]
        
        super().__init__(
            llm=llm,
            system_prompt=RESEARCH_PROMPT,
            tools=tools,
        )

    def research(self, task: str, previous_findings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform research on given task."""
        context = {
            "task": task,
            "previous_findings": previous_findings or {},
        }
        return self.run(task=task, context=context)