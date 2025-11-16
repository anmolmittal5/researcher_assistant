#!/usr/bin/env python3
"""Temporary test script to test agent orchestration with a simple query."""

import json
import os
import uuid
from langchain_core.messages import HumanMessage
from research_assistant.graph.workflow import create_workflow
from research_assistant.graph.state import AgentState

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def print_section(title: str, char: str = "="):
    """Print a formatted section header."""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")


def print_agent_output(agent_name: str, output: dict):
    """Print formatted output from an agent."""
    print_section(f"{agent_name.upper()} AGENT OUTPUT", "-")
    
    if "result" in output:
        print(f"Result:\n{output['result']}\n")
    
    if "reasoning" in output:
        print(f"Reasoning: {output['reasoning']}\n")
    
    if "decision" in output:
        print(f"Decision: {output['decision']}\n")
    
    if "traces" in output and output["traces"]:
        print("Traces:")
        for i, trace in enumerate(output["traces"], 1):
            print(f"  Iteration {i}:")
            if "thought" in trace:
                print(f"    Thought: {trace['thought']}")
            if "act" in trace:
                print(f"    Action: {trace['act']}")
            if "observation" in trace:
                obs = trace["observation"]
                if len(obs) > 500:
                    obs = obs[:500] + "... (truncated)"
                print(f"    Observation: {obs}")
        print()


def main():
    """Test agent orchestration with a simple query."""
    query = "What are the latest news in AI?"
    
    print_section("AGENT ORCHESTRATION TEST")
    print(f"Query: {query}\n")
    
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print_section("ERROR")
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these environment variables:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  export TAVILY_API_KEY='your-key-here'")
        print("\nOr create a .env file in the project root with:")
        print("  OPENAI_API_KEY=your-key-here")
        print("  TAVILY_API_KEY=your-key-here")
        return
    
    try:
        print("Creating workflow...")
        workflow = create_workflow()
        print("✓ Workflow created\n")
        
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state: AgentState = {
            "goal": query,
            "messages": [HumanMessage(content=query)],
            "tasks": [],
            "current_task": None,
            "research_results": None,
            "coder_results": None,
            "planner_results": None,
            "reporter_results": None,
            "routing_decision": None,
            "results": [],
            "traces": [],
        }
        
        print("Executing workflow...")
        print("This may take a few moments as agents process the query...\n")
        
        step_count = 0
        nodes_executed = []
        
        print("=" * 80)
        print("WORKFLOW EXECUTION STREAM".center(80))
        print("=" * 80 + "\n")
        
        for event in workflow.stream(initial_state, config, stream_mode="updates"):
            step_count += 1
            node_name = list(event.keys())[0] if event else "unknown"
            state_update = event.get(node_name, {}) if event else {}
            nodes_executed.append(node_name)
            
            print(f"\n[Step {step_count}] Executing: {node_name.upper()}")
            print("-" * 80)
            
            if "planner_results" in state_update and state_update["planner_results"]:
                print_agent_output("PLANNER", state_update["planner_results"])
                
                routing_decision = state_update.get("routing_decision", {})
                if routing_decision:
                    print(f"Routing Decision:")
                    print(f"  Next Agent: {routing_decision.get('next_agent', 'N/A')}")
                    print(f"  Reasoning: {routing_decision.get('reasoning', 'N/A')}")
                    print(f"  Task Description: {routing_decision.get('task_description', 'N/A')}")
                    print(f"  Is Complete: {routing_decision.get('is_complete', False)}\n")
            
            if "research_results" in state_update and state_update["research_results"]:
                print_agent_output("RESEARCHER", state_update["research_results"])
            
            if "coder_results" in state_update and state_update["coder_results"]:
                print_agent_output("CODER", state_update["coder_results"])
            
            if "reporter_results" in state_update and state_update["reporter_results"]:
                print_agent_output("REPORTER", state_update["reporter_results"])
        
        print(f"\n✓ Workflow execution complete. Nodes executed: {' → '.join(nodes_executed)}\n")
        
        print("=" * 80)
        print("FETCHING FINAL STATE FROM CHECKPOINTER".center(80))
        print("=" * 80 + "\n")
        
        final_state = None
        for event in workflow.stream(initial_state, config, stream_mode="values"):
            final_state = event
        
        if final_state is None:
            final_state = workflow.invoke(initial_state, config)
        
        print_section("FINAL SUMMARY")
        
        print("Workflow completed successfully!\n")
        
        if final_state.get("planner_results"):
            print_agent_output("PLANNER (Final)", final_state["planner_results"])
        
        if final_state.get("research_results"):
            print_agent_output("RESEARCHER (Final)", final_state["research_results"])
        
        if final_state.get("coder_results"):
            print_agent_output("CODER (Final)", final_state["coder_results"])
        
        if final_state.get("reporter_results"):
            print_agent_output("REPORTER (Final)", final_state["reporter_results"])
        
        print_section("FINAL ANSWER")
        if final_state.get("reporter_results") and final_state["reporter_results"].get("result"):
            print(final_state["reporter_results"]["result"])
        elif final_state.get("research_results") and final_state["research_results"].get("result"):
            print(final_state["research_results"]["result"])
        else:
            print("No final answer available in state.")
        
        if final_state.get("traces"):
            print_section("ALL TRACES")
            for trace in final_state["traces"]:
                agent = trace.get("agent", "unknown")
                iteration = trace.get("iteration", "?")
                print(f"\n[{agent.upper()}] Iteration {iteration}:")
                if "thought" in trace:
                    print(f"  Thought: {trace['thought']}")
                if "act" in trace:
                    print(f"  Action: {trace['act']}")
                if "observation" in trace:
                    obs = trace["observation"]
                    if len(obs) > 300:
                        obs = obs[:300] + "... (truncated)"
                    print(f"  Observation: {obs}")
        
        print_section("TEST COMPLETE")
        
    except Exception as e:
        print_section("ERROR")
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

