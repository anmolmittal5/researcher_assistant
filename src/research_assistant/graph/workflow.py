"""LangGraph workflow for orchestrating multi-agent ReAct system with loop-based orchestration."""

import json
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from research_assistant.graph.state import AgentState
from research_assistant.agents.planner import PlannerAgent, RoutingDecision
from research_assistant.agents.researcher import ResearchAgent
from research_assistant.agents.coder import CoderAgent
from research_assistant.agents.reporter import ReporterAgent


def sanitize_state(state_update: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all state values are JSON-serializable."""
    sanitized = {}
    for key, value in state_update.items():
        if value is None:
            sanitized[key] = None
        elif isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, (list, dict)):
            sanitized[key] = json.loads(json.dumps(value, default=str))
        else:
            sanitized[key] = str(value)
    return sanitized


_planner: PlannerAgent = None
_research: ResearchAgent = None
_coder: CoderAgent = None
_reporter: ReporterAgent = None


def create_workflow(llm: ChatOpenAI = None):
    """
    Create LangGraph workflow for multi-agent system with checkpointer.
    
    Workflow pattern:
    1. Planner decides next step using conversation history
    2. Route to appropriate agent (researcher/coder/reporter)
    3. Agent completes and results are persisted to checkpointer
    4. Loop back to planner with updated conversation history
    5. Continue until planner returns next_agent="finish"
    """
    global _planner, _research, _coder, _reporter
    
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Initialize agents
    _planner = PlannerAgent(llm=llm)
    _research = ResearchAgent(llm=llm)
    _coder = CoderAgent(llm=llm)
    _reporter = ReporterAgent(llm=llm)
    
    # Create graph with checkpointer
    checkpointer = MemorySaver()
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("reporter", reporter_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add conditional edges from planner
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "research": "research",
            "coder": "coder",
            "reporter": "reporter",
            "finish": END,
        },
    )
    
    workflow.add_edge("research", "planner")
    workflow.add_edge("coder", "planner")
    workflow.add_edge("reporter", "planner")
    
    # Compile with checkpointer
    return workflow.compile(checkpointer=checkpointer)


def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner agent node - decides next step based on conversation history and state variables."""
    goal = state.get("goal", "")
    messages = state.get("messages", [])
    
    conversation_history = messages if messages else []
    
    research_results = state.get("research_results")
    coder_results = state.get("coder_results")
    reporter_results = state.get("reporter_results")
    
    decision = _planner.decide_next_step(
        goal, 
        conversation_history,
        research_results=research_results,
        coder_results=coder_results,
        reporter_results=reporter_results
    )
    
    routing_decision = {
        "next_agent": decision.next_agent,
        "reasoning": decision.reasoning,
        "task_description": decision.task_description,
        "is_complete": decision.is_complete,
    }
    
    planner_results = {
        "decision": decision.next_agent,
        "reasoning": decision.reasoning,
    }
    
    planner_message = AIMessage(
        content=f"Planner Decision: {decision.reasoning}\nNext Agent: {decision.next_agent}\nTask: {decision.task_description or goal}"
    )
    
    updated_messages = list(state.get("messages", []))
    updated_messages.append(planner_message)
    
    return sanitize_state({
        "routing_decision": routing_decision,
        "planner_results": planner_results,
        "next_agent": decision.next_agent,
        "current_task": decision.task_description or goal,
        "messages": updated_messages,
        "traces": state.get("traces", []),
    })


def research_node(state: AgentState) -> Dict[str, Any]:
    """Research agent node - gathers evidence from web and documents."""
    routing_decision = state.get("routing_decision", {})
    task = routing_decision.get("task_description") or state.get("current_task") or state.get("goal", "")
    
    result = _research.research(
        task=task,
        previous_findings=state.get("research_results"),
    )
    
    research_message = AIMessage(
        content=f"Research Agent Results:\n{result.get('result', 'No results')}"
    )
    
    updated_messages = list(state.get("messages", []))
    updated_messages.append(research_message)
    
    traces_with_agent = []
    for trace in result.get("traces", []):
        trace["agent"] = "research"
        traces_with_agent.append(trace)
    
    return sanitize_state({
        "research_results": result,
        "results": state.get("results", []) + [{"type": "research", "data": result}],
        "traces": state.get("traces", []) + traces_with_agent,
        "current_task": task,
        "messages": updated_messages,
    })


def coder_node(state: AgentState) -> Dict[str, Any]:
    """Coder agent node - executes Python code for validation."""
    routing_decision = state.get("routing_decision", {})
    task = routing_decision.get("task_description") or state.get("current_task") or state.get("goal", "")
    
    coder_results = state.get("coder_results") or {}
    previous_code = coder_results.get("result", "") if isinstance(coder_results, dict) else ""
    
    result = _coder.code(
        task=task,
        previous_code=previous_code,
    )
    
    # Add coder results to messages
    coder_message = AIMessage(
        content=f"Coder Agent Results:\n{result.get('result', 'No results')}"
    )
    
    # Update messages list
    updated_messages = list(state.get("messages", []))
    updated_messages.append(coder_message)
    
    # Add agent name to traces
    traces_with_agent = []
    for trace in result.get("traces", []):
        trace["agent"] = "coder"
        traces_with_agent.append(trace)
    
    return sanitize_state({
        "coder_results": result,
        "results": state.get("results", []) + [{"type": "coder", "data": result}],
        "traces": state.get("traces", []) + traces_with_agent,
        "current_task": task,  # Keep task for reporter
        "messages": updated_messages,
    })


def reporter_node(state: AgentState) -> Dict[str, Any]:
    """Reporter agent node - synthesizes final response from research and code results."""
    question = state.get("goal", "")
    research_results = state.get("research_results")
    coder_results = state.get("coder_results")
    
    result = _reporter.synthesize(
        question=question,
        research_findings=research_results,
        coder_results=coder_results,
    )
    
    reporter_message = AIMessage(
        content=f"Reporter Agent Results (Final Answer):\n{result.get('result', 'No results')}"
    )
    
    updated_messages = list(state.get("messages", []))
    updated_messages.append(reporter_message)
    
    traces_with_agent = []
    for trace in result.get("traces", []):
        trace["agent"] = "reporter"
        traces_with_agent.append(trace)
    
    return sanitize_state({
        "reporter_results": result,
        "traces": state.get("traces", []) + traces_with_agent,
        "is_complete": True,
        "messages": updated_messages,
    })


def route_after_planner(state: AgentState) -> Literal["research", "coder", "reporter", "finish"]:
    """Route to next agent after planner execution based on routing decision."""
    routing_decision = state.get("routing_decision", {})
    next_agent = routing_decision.get("next_agent") or state.get("next_agent", "finish")
    
    agent_mapping = {
        "researcher": "research",
        "coder": "coder",
        "reporter": "reporter",
        "finish": "finish"
    }
    
    mapped_agent = agent_mapping.get(next_agent, next_agent)
    
    if mapped_agent not in ["research", "coder", "reporter", "finish"]:
        return "finish" 
    
    return mapped_agent

