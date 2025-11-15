"""Coder agent for executing Python code and validation."""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from research_assistant.agents.base import BaseReActAgent
from research_assistant.prompts.coder import CODER_PROMPT
from research_assistant.tools import get_python_repl_tool


class CoderAgent(BaseReActAgent):
    """Agent that executes Python code for validation and data transformation."""

    def __init__(self, llm: ChatOpenAI = None):
        """Initialize Coder agent with LLM and Python REPL tool."""
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        super().__init__(
            llm=llm,
            system_prompt=CODER_PROMPT,
            tools=[get_python_repl_tool()],
        )

    def code(self, task: str, previous_code: str = None) -> Dict[str, Any]:
        """Execute coding task."""
        context = {
            "task": task,
            "previous_code": previous_code or "",
        }
        return self.run(task=task, context=context)