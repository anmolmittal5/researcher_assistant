"""Research agent for gathering evidence from web and documents."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from research_assistant.agents.base import BaseReActAgent
from research_assistant.prompts.research import RESEARCH_PROMPT
from research_assistant.tools import get_tavily_tool, get_drive_mcp_tools


class ResearchAgent(BaseReActAgent):
    """Agent that gathers evidence using Tavily Search and Google Drive via MCP."""

    def __init__(self, llm: ChatOpenAI = None, use_drive: bool = False):
        """Initialize Research agent with LLM and tools."""
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        tools: List = [get_tavily_tool()]
        if use_drive:
            try:
                drive_tools = get_drive_mcp_tools()
                tools.extend(drive_tools)
            except Exception as e:
                print(f"Warning: Could not load Drive MCP tools: {e}")
        
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