"""Streamlit UI for Research Assistant with real-time streaming."""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from research_assistant.graph import create_workflow, AgentState
from research_assistant.graph.state import AgentState as StateType

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
    """Format a ReAct trace for display."""
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


def display_logs(logs_container, traces: List[Dict[str, Any]], current_agent: str = ""):
    """Display ReAct traces in the logs container (only Research and Coder agents)."""
    with logs_container:
        if not traces:
            st.info("No execution traces yet. Submit a query to see agent reasoning.")
            return
        
        st.markdown("### 🔄 Agent Execution Logs")
        st.markdown("*Showing Research and Coder agent traces*")
        st.markdown("---")
        
        filtered_traces = [
            trace for trace in traces 
            if trace.get("agent", "").lower() in ["research", "coder"]
        ]
        
        if not filtered_traces:
            st.info("No Research or Coder agent traces yet.")
            return
        
        for i, trace in enumerate(filtered_traces):
            agent = trace.get("agent", current_agent)
            st.markdown(format_trace(trace, agent), unsafe_allow_html=True)


def run_workflow_streaming(goal: str, chat_container, logs_container):
    """Run workflow with streaming updates."""
    try:
        # Initialize workflow
        workflow = create_workflow()
        
        # Initial state
        initial_state: AgentState = {
            "goal": goal,
            "plan": None,
            "tasks": [],
            "current_task": None,
            "research_results": None,
            "coder_results": None,
            "planner_results": None,
            "reporter_results": None,
            "results": [],
            "traces": [],
            "next_agent": None,
            "is_complete": False,
        }
        
        ai_placeholder = chat_container.empty()
        
        # Stream workflow execution
        all_traces = []
        
        with ai_placeholder.chat_message("assistant"):
            response_placeholder = st.empty()
            response_text = "🤔 Processing your request..."
            response_placeholder.markdown(response_text)
        
        # Execute workflow with streaming
        try:
            final_state = workflow.invoke(initial_state)
            
            all_traces = final_state.get("traces", [])
            
            for i in range(len(all_traces)):
                display_logs(logs_container, all_traces[:i+1])
                time.sleep(0.2)
            
            reporter_results = final_state.get("reporter_results")
            research_results = final_state.get("research_results")
            coder_results = final_state.get("coder_results")
            
            if reporter_results:
                final_response = reporter_results.get("result", "")
            else:
                final_response = "✅ **Task Complete!**\n\n"
                if research_results:
                    research_content = research_results.get("result", "")
                    if research_content:
                        final_response += f"**Research Findings:**\n\n{research_content}\n\n"
                if coder_results:
                    code_content = coder_results.get("result", "")
                    if code_content:
                        final_response += f"**Code Execution:**\n\n{code_content}\n\n"
            
            ai_placeholder.empty()
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(final_response)
            
            return final_state
            
        except Exception as e:
            error_msg = f"❌ **Error during execution:**\n\n{str(e)}"
            ai_placeholder.empty()
            with chat_container:
                with st.chat_message("assistant"):
                    st.error(error_msg)
            raise
            
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
            st.rerun()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "traces" not in st.session_state:
        st.session_state.traces = []
    
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
                if reporter_results:
                    response_content = reporter_results.get("result", "")
                else:
                    response_content = result.get("plan", "Task completed.")
                
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content
                })
                st.session_state.traces = result.get("traces", [])
                st.rerun()
    
    with col2:
        st.markdown("### 📊 Execution Logs")
        logs_display = st.container(height=700)
        if st.session_state.traces:
            display_logs(logs_display, st.session_state.traces)
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

