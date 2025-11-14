# ui/streamlit_app.py
"""
Pre-final (simple) Streamlit UI for Research Assistant.
This lightweight version is safe to push now and later can be replaced with the final version.
"""

import os
import sys
from pathlib import Path
import streamlit as st

# make sure repo root is importable for the planner stub
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Try to import the planner stub if present; otherwise use a local fallback
try:
    from src.research_assistant.agents.planner_agent import plan as planner_plan
except Exception:
    planner_plan = None

st.set_page_config(page_title="Research Assistant (Pre-final)", layout="wide")

st.title("🔬 Research Assistant — (Pre-final UI)")
st.markdown("This is a lightweight scaffold version intended for early testing and submission.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "traces" not in st.session_state:
    st.session_state.traces = []

# Simple two-column layout
col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.header("Conversation")
    # Show chat history
    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        if role == "user":
            st.markdown(f"**You:** {msg.get('content')}")
        else:
            st.markdown(f"**Assistant:** {msg.get('content')}")
    
    user_input = st.text_input("Enter a research query or task", "")
    
    if st.button("Run ReAct") or user_input:
        if user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})
        else:
            user_input = ""
        
        # Basic stubbed planner behavior: generate a prompt or simple plan
        if planner_plan:
            prompt_text = planner_plan(user_input or "Sample goal for planner")
            assistant_text = "Planner prompt generated (see logs)."
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            # Save a very simple trace using planner prompt as an observation
            st.session_state.traces.append({
                "agent": "planner",
                "thought": "Generated plan prompt",
                "act": "Create prompt for specialist agents",
                "observation": prompt_text[:800]
            })
        else:
            # Fallback simple plan
            plan_text = (
                "Thought: Break the goal into Research and Coder tasks.\n"
                "Act: Route research subtasks to Research agent.\n"
                "Act: Route coding subtasks to Coder agent.\n"
                "Observation: Placeholder (planner stub not available).\n"
            )
            st.session_state.messages.append({"role": "assistant", "content": "Planner (stub) executed — see logs."})
            st.session_state.traces.append({
                "agent": "planner",
                "thought": "Decompose goal into research and code tasks",
                "act": "Route to Research and Coder agents",
                "observation": "Planner stub used; no external LLM called"
            })

        # trigger a re-run to show updated logs & chat
        st.experimental_rerun()

with col2:
    st.header("Execution Logs")
    if not st.session_state.traces:
        st.info("Execution logs will appear here after running the planner.")
    else:
        # Show traces in reverse chronological order
        for trace in reversed(st.session_state.traces[-10:]):
            agent = trace.get("agent", "agent")
            st.markdown(f"**Agent:** {agent}")
            if trace.get("thought"):
                st.markdown(f"- 💭 **Thought:** {trace['thought']}")
            if trace.get("act"):
                st.markdown(f"- ⚡ **Act:** {trace['act']}")
            if trace.get("observation"):
                obs = str(trace["observation"])
                if len(obs) > 600:
                    obs = obs[:600] + "..."
                st.markdown(f"- 👁️ **Observation:** {obs}")
            st.markdown("---")

# Footer instructions
st.markdown(
    "----\n"
    "This is a minimal, pushable UI. Replace with final UI later and push the final version as a separate commit."
)
