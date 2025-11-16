"""State definition for LangGraph multi-agent workflow."""

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """State shared across all agents in the workflow."""
    
    goal: str
    messages: List[BaseMessage]
    tasks: List[str]
    current_task: Optional[str]
    research_results: Optional[Dict[str, Any]]
    coder_results: Optional[Dict[str, Any]]
    planner_results: Optional[Dict[str, Any]]
    reporter_results: Optional[Dict[str, Any]]
    routing_decision: Optional[Dict[str, Any]]
    results: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]

