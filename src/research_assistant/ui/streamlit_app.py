# ui/streamlit_app.py

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from streamlit_option_menu import option_menu

# make sure repo root is importable for the planner stub
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Try to import the planner stub if present; otherwise use a local fallback
try:
    from src.research_assistant.agents.planner_agent import plan as planner_plan
except Exception:
    planner_plan = None

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better interactivity
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-planner {
        background-color: #ff9800;
        color: white;
    }
    .badge-research {
        background-color: #2196f3;
        color: white;
    }
    .badge-coder {
        background-color: #9c27b0;
        color: white;
    }
    .trace-container {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }
    .trace-section {
        margin-top: 0.5rem;
    }
    .expandable-content {
        max-height: 300px;
        overflow-y: auto;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    .status-active {
        background-color: #4caf50;
        animation: pulse 1.5s infinite;
    }
    .status-idle {
        background-color: #9e9e9e;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

st.title("🔬 Research Assistant")
st.markdown("Multi-agent ReAct system for research and code generation")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "traces" not in st.session_state:
    st.session_state.traces = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gpt-4o"
if "google_drive_enabled" not in st.session_state:
    st.session_state.google_drive_enabled = False
if "trace_expanded" not in st.session_state:
    st.session_state.trace_expanded = {}

# Sidebar with settings and controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Model selection
    models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    selected_model = st.selectbox(
        "🤖 Model",
        models,
        index=models.index(st.session_state.selected_model) if st.session_state.selected_model in models else 0
    )
    st.session_state.selected_model = selected_model
    
    # Google Drive toggle
    google_drive = st.checkbox(
        "📁 Enable Google Drive",
        value=st.session_state.google_drive_enabled,
        help="Enable Google Drive integration for document access"
    )
    st.session_state.google_drive_enabled = google_drive
    
    st.divider()
    
    # Session controls
    st.subheader("📊 Session Info")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Traces", len(st.session_state.traces))
    
    if st.session_state.processing:
        st.status("⏳ Processing...", state="running")
    
    st.divider()
    
    # Action buttons
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.traces = []
        st.session_state.trace_expanded = {}
        st.rerun()
    
    if st.button("📥 Export Conversation", use_container_width=True):
        export_data = {
            "messages": st.session_state.messages,
            "traces": st.session_state.traces,
            "timestamp": datetime.now().isoformat(),
            "model": st.session_state.selected_model
        }
        st.download_button(
            label="💾 Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    st.divider()
    
    # Tips and help
    with st.expander("💡 Tips"):
        st.markdown("""
        - Enter a research query to start
        - Watch execution logs in real-time
        - Click on traces to expand details
        - Export conversations for later review
        """)
    
    with st.expander("❓ Example Queries"):
        example_queries = [
            "Research ReAct methodology and summarize key findings",
            "Find recent papers on transformer architectures",
            "Search for best practices in multi-agent systems"
        ]
        for i, query in enumerate(example_queries):
            if st.button(query, key=f"example_{i}", use_container_width=True):
                st.session_state.example_query = query
                st.rerun()

# Main layout - two columns
col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.header("💬 Conversation")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages with better formatting
        for idx, msg in enumerate(st.session_state.messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                st.markdown(
                    f'<div class="user-message">'
                    f'<strong>👤 You</strong>'
                    f'{f" <small style="color: #666;">({timestamp})</small>" if timestamp else ""}'
                    f'<br>{content}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                # Add copy button for assistant messages
                col_msg, col_copy = st.columns([10, 1])
                with col_msg:
                    st.markdown(
                        f'<div class="assistant-message">'
                        f'<strong>🤖 Assistant</strong>'
                        f'{f" <small style="color: #666;">({timestamp})</small>" if timestamp else ""}'
                        f'<br>{content}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with col_copy:
                    if st.button("📋", key=f"copy_{idx}", help="Copy to clipboard"):
                        st.code(content, language=None)
    
    # Processing indicator
    if st.session_state.processing:
        st.info("🔄 Processing your request...")
        st.progress(0.5)
    
    st.divider()
    
    # Input area with improved UX
    query_input = st.text_area(
        "Enter your research query or task",
        value=st.session_state.get("example_query", ""),
        height=100,
        placeholder="e.g., Research ReAct methodology and summarize key findings...",
        key="query_input"
    )
    
    # Clear example query after use
    if "example_query" in st.session_state:
        st.session_state.example_query = ""
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    with col_btn1:
        run_button = st.button("🚀 Run ReAct", type="primary", use_container_width=True)
    
    with col_btn2:
        regenerate_button = st.button("🔄 Regenerate", use_container_width=True, disabled=len(st.session_state.messages) == 0)
    
    with col_btn3:
        clear_input = st.button("🗑️ Clear", use_container_width=True)
        if clear_input:
            st.session_state.query_input = ""
            st.rerun()
    
    # Handle regenerate: remove last assistant message and reuse last user query
    if regenerate_button and len(st.session_state.messages) > 0:
        # Remove last assistant message if exists
        if st.session_state.messages and st.session_state.messages[-1].get("role") == "assistant":
            st.session_state.messages.pop()
        # Get last user message
        last_user_msg = next(
            (msg for msg in reversed(st.session_state.messages) if msg.get("role") == "user"),
            None
        )
        if last_user_msg:
            query_input = last_user_msg.get("content", "")
            run_button = True
    
    # Process query
    if run_button and query_input.strip():
        st.session_state.processing = True
        
        # Add user message (only if not regenerating)
        if not regenerate_button:
            user_message = {
                "role": "user",
                "content": query_input.strip(),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.messages.append(user_message)
        
        # Process with planner
        if planner_plan:
            with st.spinner("Generating plan..."):
                try:
                    prompt_text = planner_plan(query_input.strip())
                    assistant_text = f"✅ Planner generated a plan. Check the execution logs for details.\n\n**Summary:** The goal has been decomposed into actionable tasks for specialist agents."
                    st.session_state.traces.append({
                        "agent": "planner",
                        "thought": "Generated plan prompt",
                        "act": "Create prompt for specialist agents",
                        "observation": prompt_text[:800] if len(prompt_text) > 800 else prompt_text,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                except Exception as e:
                    assistant_text = f"❌ Error: {str(e)}"
        else:
            assistant_text = (
                "✅ Planner (stub) executed. Breaking goal into tasks:\n\n"
                "- **Research tasks**: Route to Research agent\n"
                "- **Coding tasks**: Route to Coder agent\n\n"
                "See execution logs for details."
            )
            st.session_state.traces.append({
                "agent": "planner",
                "thought": "Decompose goal into research and code tasks",
                "act": "Route to Research and Coder agents",
                "observation": "Planner stub used; no external LLM called",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
        
        # Add assistant message
        assistant_message = {
            "role": "assistant",
            "content": assistant_text,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(assistant_message)
        
        st.session_state.processing = False
        st.rerun()

with col2:
    st.header("📊 Execution Logs")
    
    if not st.session_state.traces:
        st.info("📝 Execution logs will appear here after running the planner.")
    else:
        # Filter and search
        agent_filter = st.multiselect(
            "Filter by agent",
            options=["planner", "research", "coder"],
            default=[],
            label_visibility="collapsed"
        )
        
        # Show traces in reverse chronological order
        filtered_traces = st.session_state.traces
        if agent_filter:
            filtered_traces = [t for t in filtered_traces if t.get("agent", "").lower() in agent_filter]
        
        for idx, trace in enumerate(reversed(filtered_traces[-10:])):
            trace_id = len(filtered_traces) - idx - 1
            agent = trace.get("agent", "agent").lower()
            timestamp = trace.get("timestamp", "")
            
            # Agent badge with color
            badge_class = {
                "planner": "badge-planner",
                "research": "badge-research",
                "coder": "badge-coder"
            }.get(agent, "")
            
            agent_display = agent.capitalize()
            
            # Expandable trace container
            expander_label = f"🔷 {agent_display}"
            if timestamp:
                expander_label += f" ({timestamp})"
            with st.expander(
                expander_label,
                expanded=st.session_state.trace_expanded.get(trace_id, True)
            ):
                st.markdown(
                    f'<span class="agent-badge {badge_class}">{agent_display}</span>',
                    unsafe_allow_html=True
                )
                if trace.get("thought"):
                    st.markdown("**💭 Thought:**")
                    st.info(trace['thought'])
                
                if trace.get("act"):
                    st.markdown("**⚡ Act:**")
                    st.warning(trace['act'])
                
                if trace.get("observation"):
                    obs = str(trace["observation"])
                    st.markdown("**👁️ Observation:**")
                    if len(obs) > 500:
                        with st.expander("View full observation"):
                            st.text(obs)
                        st.text(obs[:500] + "...")
                    else:
                        st.text(obs)
                
                # Delete trace button
                if st.button("🗑️ Delete", key=f"delete_trace_{trace_id}", help="Delete this trace"):
                    # Find and remove the trace
                    original_idx = len(st.session_state.traces) - trace_id - 1
                    if 0 <= original_idx < len(st.session_state.traces):
                        st.session_state.traces.pop(original_idx)
                    st.rerun()
        
        if len(filtered_traces) > 10:
            st.caption(f"Showing last 10 of {len(filtered_traces)} traces")

# Footer
st.divider()
col_foot1, col_foot2 = st.columns([3, 1])
with col_foot1:
    st.caption("🔬 Research Assistant - Multi-agent ReAct system")
with col_foot2:
    st.caption(f"Model: {st.session_state.selected_model}")


def main():
    """
    Entry point for the research assistant Streamlit app.
    This function is called when running via the poetry script entry point.
    """
    import subprocess
    import sys
    app_path = Path(__file__).resolve()
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    # When run directly, Streamlit will execute the script
    pass
