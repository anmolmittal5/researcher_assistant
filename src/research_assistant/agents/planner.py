"""Planner agent for goal decomposition and task routing."""

from typing import Dict, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from research_assistant.agents.base import BaseReActAgent
from research_assistant.prompts.planner import PLANNER_PROMPT


class PlannerAgent(BaseReActAgent):
    """Agent that decomposes goals and routes tasks to specialist agents."""

    def __init__(self, llm: ChatOpenAI = None):
        """Initialize Planner agent with LLM."""
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        super().__init__(
            llm=llm,
            system_prompt=PLANNER_PROMPT,
            tools=[],
        )

    def plan(self, goal: str, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Decompose goal and create execution plan."""
        state = state or {}
        previous_results = state.get("results", [])
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        planning_prompt = f"""You are a Planner agent. Analyze the user's goal and create an execution plan.

Goal: {goal}
Previous Results: {previous_results}
Current date and time: {current_time}

Create a brief plan for how to accomplish this goal. Identify which specialist agents (Research, Coder) should be involved.

Respond with just a concise plan (2-3 sentences)."""
        
        response = self.llm.invoke(planning_prompt)
        plan_text = response.content
        
        return {
            "result": plan_text,
            "traces": [{
                "iteration": 1,
                "thought": plan_text,
                "act": "plan_created",
                "observation": "",
            }],
            "final_act": "plan_created",
        }

    def should_route_to_research(self, task: str) -> bool:
        """Determine if task requires research agent."""
        if not task:
            return False
        research_keywords = [
            "research", "search", "find", "information", "document", 
            "news", "latest", "recent", "what", "who", "when", "where", 
            "how", "why", "ai", "artificial intelligence"
        ]
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in research_keywords)

    def should_route_to_coder(self, task: str) -> bool:
        """Determine if task requires coder agent."""
        if not task:
            return False
        coder_keywords = ["code", "validate", "calculate", "execute", "script"]
        return any(keyword in task.lower() for keyword in coder_keywords)

