"""Streamlit UI for Research Assistant with real-time streaming."""

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from research_assistant.graph import create_workflow
from research_assistant.graph.state import AgentState
from langchain_core.messages import HumanMessage

load_dotenv()

st.set_page_config(
    page_title="Cognivia",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .planner-badge { background-color: #e3f2fd; color: #1976d2; }
    .research-badge { background-color: #f3e5f5; color: #7b1fa2; }
    .coder-badge { background-color: #e8f5e9; color: #388e3c; }
    .reporter-badge { background-color: #fff3e0; color: #e65100; }
    .trace-container {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .thought-text { color: #1976d2; font-weight: 500; }
    .act-text { color: #f57c00; font-weight: 500; }
    .observation-text { color: #388e3c; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


def get_agent_badge(agent_name: str) -> str:
    """Get styled badge for agent name."""
    badges = {
        "planner": '<span class="agent-badge planner-badge">📋 Planner</span>',
        "research": '<span class="agent-badge research-badge">🔍 Research</span>',
        "coder": '<span class="agent-badge coder-badge">💻 Coder</span>',
        "reporter": '<span class="agent-badge reporter-badge">📝 Reporter</span>',
    }
    return badges.get(agent_name.lower(), f'<span class="agent-badge">{agent_name}</span>')


def format_trace(trace: Dict[str, Any], agent_name: str = "") -> str:
    """Format a ReAct trace for display - no truncation for observations."""
    html = f'<div class="trace-container">'
    if agent_name:
        html += get_agent_badge(agent_name)
    
    if trace.get("thought"):
        html += f'<div class="thought-text"><strong>💭 Thought:</strong> {trace["thought"]}</div>'
    
    if trace.get("act"):
        html += f'<div class="act-text"><strong>⚡ Act:</strong> {trace["act"]}</div>'
    
    if trace.get("observation"):
        obs = str(trace["observation"])
        html += f'<div class="observation-text"><strong>👁️ Observation:</strong> {obs}</div>'
    
    html += '</div>'
    return html


def display_logs(logs_container, traces: List[Dict[str, Any]], state: Dict[str, Any] = None, current_agent: str = ""):
    """Display ReAct traces and full results in the logs container (only Research and Coder agents)."""
    with logs_container:
        if not traces and not state:
            st.info("No execution traces yet. Submit a query to see agent reasoning.")
            return
        
        st.markdown("### 🔄 Agent Execution Logs")
        st.markdown("*Showing Research and Coder agent traces and outputs*")
        st.markdown("---")
        
        if state and state.get("research_results"):
            research_results = state.get("research_results", {})
            st.markdown(get_agent_badge("research"), unsafe_allow_html=True)
            st.markdown("**Research Agent Final Output:**")
            research_result = research_results.get("result", "")
            if research_result:
                with st.container():
                    st.markdown("---")
                    st.markdown(research_result)
                    st.markdown("---")
            else:
                st.info("Research completed but no result content available.")
            st.markdown("---")
        
        if state and state.get("coder_results"):
            coder_results = state.get("coder_results", {})
            st.markdown(get_agent_badge("coder"), unsafe_allow_html=True)
            st.markdown("**Coder Agent Final Output:**")
            coder_result = coder_results.get("result", "")
            if coder_result:

                with st.container():
                    st.markdown("---")
                    st.markdown(coder_result)
                    st.markdown("---")
            else:
                st.info("Code execution completed but no result content available.")
            st.markdown("---")
        
        filtered_traces = [
            trace for trace in traces 
            if trace.get("agent", "").lower() in ["research", "coder"]
        ]
        
        if filtered_traces:
            st.markdown("**Detailed Execution Traces:**")
            for i, trace in enumerate(filtered_traces):
                agent = trace.get("agent", current_agent)
                st.markdown(format_trace(trace, agent), unsafe_allow_html=True)
        elif not state or (not state.get("research_results") and not state.get("coder_results")):
            st.info("No Research or Coder agent traces yet.")


def run_workflow_streaming(goal: str, chat_container, logs_container):
    """Run workflow with streaming updates."""
    try:
        # Initialize workflow
        workflow = create_workflow()
        
        initial_state: AgentState = {
            "goal": goal,
            "messages": [HumanMessage(content=goal)],
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
        
        ai_placeholder = chat_container.empty()
        
        all_traces = []
        
        with ai_placeholder.chat_message("assistant"):
            response_placeholder = st.empty()
            response_text = "🤔 Processing your request..."
            response_placeholder.markdown(response_text)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            final_state = workflow.invoke(initial_state, config, debug_mode=True)
            
            if not final_state:
                raise ValueError("Workflow returned empty state")
            
            all_traces = final_state.get("traces", [])
            
            for i in range(len(all_traces)):
                display_logs(logs_container, all_traces[:i+1], final_state)
                time.sleep(0.2)
            
            display_logs(logs_container, all_traces, final_state)
            
            reporter_results = final_state.get("reporter_results")
            research_results = final_state.get("research_results")
            coder_results = final_state.get("coder_results")
            
            if reporter_results:
                final_response = reporter_results.get("result", "")
                if not final_response:
                    messages = final_state.get("messages", [])
                    for msg in reversed(messages):
                        if hasattr(msg, 'content'):
                            content = str(msg.content)
                            if "Reporter Agent Results (Final Answer):" in content:
                                final_response = content.split("Reporter Agent Results (Final Answer):\n", 1)[-1]
                                break
                    if not final_response:
                        final_response = "Reporter completed but no result content available."
            else:
                final_response = ""
                if research_results:
                    research_content = research_results.get("result", "")
                    if research_content:
                        final_response += f"**Research Findings:**\n\n{research_content}\n\n"
                if coder_results:
                    code_content = coder_results.get("result", "")
                    if code_content:
                        final_response += f"**Code Execution:**\n\n{code_content}\n\n"
                
                if not final_response:
                    messages = final_state.get("messages", [])
                    if messages:
                        for msg in reversed(messages):
                            if hasattr(msg, 'content'):
                                content = str(msg.content)
                                if "Reporter Agent Results (Final Answer):" in content:
                                    final_response = content.split("Reporter Agent Results (Final Answer):\n", 1)[-1]
                                    break
                                elif "Research Agent Results:" in content:
                                    final_response = content.split("Research Agent Results:\n", 1)[-1]
                                    break
                                elif "Coder Agent Results:" in content:
                                    final_response = content.split("Coder Agent Results:\n", 1)[-1]
                                    break
                
                if not final_response:
                    final_response = "Task completed. Processing results..."
            
            ai_placeholder.empty()
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(final_response)
            
            return final_state
            
        except Exception as e:
            import traceback
            error_msg = f"❌ **Error during execution:**\n\n{str(e)}\n\n**Traceback:**\n```\n{traceback.format_exc()}\n```"
            ai_placeholder.empty()
            with chat_container:
                with st.chat_message("assistant"):
                    st.error(error_msg)
            return None
            
    except Exception as e:
        st.error(f"Failed to initialize workflow: {str(e)}")
        return None


def main():
    """Main Streamlit application."""
    st.markdown('<div class="main-header">Cognivia</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-top: -1rem; margin-bottom: 2rem;">Your personal research assistant</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    with st.sidebar:
        st.header("⚙️ Settings")
        
        model = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4.1", "gpt-4.1-nano"],
            index=0,
            disabled=True
        )
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.traces = []
            st.session_state.last_state = {}
            st.rerun()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "traces" not in st.session_state:
        st.session_state.traces = []
    if "last_state" not in st.session_state:
        st.session_state.last_state = {}
    
    col1, col2 = st.columns([2, 1], gap="medium")
    
    with col1:
        st.markdown("### 💬 Conversation")
        chat_container = st.container()
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        user_input = st.chat_input("Enter your research query or task...")
        
        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Create logs container in the right column
            with col2:
                logs_container = st.container(height=700)
            
            result = run_workflow_streaming(
                user_input,
                chat_container,
                logs_container
            )
            
            if result:
                reporter_results = result.get("reporter_results")
                research_results = result.get("research_results")
                coder_results = result.get("coder_results")
                
                if reporter_results:
                    response_content = reporter_results.get("result", "")
                else:
                    response_content = "✅ **Task Complete!**\n\n"
                    if research_results:
                        research_content = research_results.get("result", "")
                        if research_content:
                            response_content += f"**Research Findings:**\n\n{research_content}\n\n"
                    if coder_results:
                        code_content = coder_results.get("result", "")
                        if code_content:
                            response_content += f"**Code Execution:**\n\n{code_content}\n\n"
                    
                    if response_content == "✅ **Task Complete!**\n\n":
                        messages = result.get("messages", [])
                        if messages:
                            for msg in reversed(messages):
                                if hasattr(msg, 'content'):
                                    content = str(msg.content)
                                    if "Reporter Agent Results" in content or "Research Agent Results" in content or "Coder Agent Results" in content:
                                        if "Reporter Agent Results" in content:
                                            response_content = content.split("Reporter Agent Results (Final Answer):\n", 1)[-1]
                                        elif "Research Agent Results" in content:
                                            response_content = content.split("Research Agent Results:\n", 1)[-1]
                                        elif "Coder Agent Results" in content:
                                            response_content = content.split("Coder Agent Results:\n", 1)[-1]
                                        break
                        
                    if not response_content or response_content == "✅ **Task Complete!**\n\n":
                        response_content = "Task completed. No results available."
                
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content
                })
                st.session_state.traces = result.get("traces", [])
                st.session_state.last_state = result
                st.rerun()
    
    with col2:
        st.markdown("### 📊 Execution Logs")
        logs_display = st.container(height=700)
        if st.session_state.traces or st.session_state.get("last_state"):
            last_state = st.session_state.get("last_state", {})
            display_logs(logs_display, st.session_state.traces, last_state)
        else:
            logs_display.info("💡 Execution logs will appear here as agents process your query.")


if __name__ == "__main__":
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        st.info("Please set these in your `.env` file. See `env.example` for reference.")
        st.stop()
    
    main()

