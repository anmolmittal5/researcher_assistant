"""State definition for LangGraph multi-agent workflow."""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """State shared across all agents in the workflow."""
    
    goal: str
    plan: Optional[str]
    tasks: List[str]
    current_task: Optional[str]
    research_results: Optional[Dict[str, Any]]
    coder_results: Optional[Dict[str, Any]]
    planner_results: Optional[Dict[str, Any]]
    reporter_results: Optional[Dict[str, Any]]
    results: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]

