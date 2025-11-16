"""Streamlit UI for Research Assistant with real-time streaming."""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from research_assistant.graph import create_workflow, AgentState
from research_assistant.graph.state import AgentState as StateType

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
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
        obs = str(trace["observation"])[:500]  # Truncate long observations
        if len(str(trace["observation"])) > 500:
            obs += "..."
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
        
        # Filter to show only Research and Coder traces
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
        
        # Create placeholder for AI response
        ai_placeholder = chat_container.empty()
        
        # Stream workflow execution
        all_traces = []
        
        # Show initial processing message
        with ai_placeholder.chat_message("assistant"):
            response_placeholder = st.empty()
            response_text = "🤔 Processing your request..."
            response_placeholder.markdown(response_text)
        
        # Execute workflow with streaming
        try:
            # Use astream for real-time updates if available
            # For now, we'll use invoke and update UI incrementally
            final_state = workflow.invoke(initial_state)
            
            # Collect all traces
            all_traces = final_state.get("traces", [])
            
            # Update logs incrementally for visual effect
            for i in range(len(all_traces)):
                display_logs(logs_container, all_traces[:i+1])
                time.sleep(0.2)  # Small delay for visual streaming effect
            
            # Extract reporter results (final synthesized response)
            reporter_results = final_state.get("reporter_results")
            research_results = final_state.get("research_results")
            coder_results = final_state.get("coder_results")
            
            # Build final response from Reporter agent
            if reporter_results:
                final_response = reporter_results.get("result", "")
            else:
                # Fallback if reporter didn't run (shouldn't happen)
                final_response = "✅ **Task Complete!**\n\n"
                if research_results:
                    research_content = research_results.get("result", "")
                    if research_content:
                        final_response += f"**Research Findings:**\n\n{research_content}\n\n"
                if coder_results:
                    code_content = coder_results.get("result", "")
                    if code_content:
                        final_response += f"**Code Execution:**\n\n{code_content}\n\n"
            
            # Update final response in chat
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
    # Header
    st.markdown('<div class="main-header">🔬 Research Assistant</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection (for future use)
        model = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0,
            disabled=True  # Currently fixed to gpt-4o
        )
        
        # Options
        st.subheader("Options")
        use_drive = st.checkbox("Enable Google Drive", value=False)
        show_raw_traces = st.checkbox("Show Raw Traces", value=False)
        
        st.markdown("---")
        st.info("💡 **Tip:** Enable Google Drive to search internal documents alongside web research.")
        
        # Clear button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.traces = []
            st.rerun()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "traces" not in st.session_state:
        st.session_state.traces = []
    
    # Main layout: Chat on left, Logs on right
    col1, col2 = st.columns([2, 1], gap="medium")
    
    with col1:
        st.markdown("### 💬 Conversation")
        chat_container = st.container()
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Input area
        user_input = st.chat_input("Enter your research query or task...")
        
        if user_input:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Create logs container in the right column
            with col2:
                logs_container = st.container(height=700)
            
            # Run workflow with streaming
            result = run_workflow_streaming(
                user_input,
                chat_container,
                logs_container
            )
            
            if result:
                # Extract reporter results for chat history
                reporter_results = result.get("reporter_results")
                if reporter_results:
                    response_content = reporter_results.get("result", "")
                else:
                    # Fallback
                    response_content = result.get("plan", "Task completed.")
                
                # Add assistant response to history (Reporter output)
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
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        st.info("Please set these in your `.env` file. See `env.example` for reference.")
        st.stop()
    
    main()

