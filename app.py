"""
TalentScout Hiring Assistant — Streamlit App
=============================================
Entry point for the chatbot UI.

Layout:
    • Wide mode with a sidebar showing a live candidate card + progress bar.
    • Main column renders the chat using native ``st.chat_message`` bubbles.
    • ``st.chat_input`` serves as the input widget.
    • Custom CSS is injected for brand polish.
"""

import sys
import os
import json
import hashlib
from datetime import datetime

import streamlit as st

# Ensure project root is on sys.path so relative imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.state_machine import StateMachine, ConversationState
from chatbot.llm_client import is_llm_available
from data.session_store import save_session
from utils.security import mask_email, mask_phone, hash_session_id


# Page config & custom CSS

st.set_page_config(
    page_title="TalentScout — AI Hiring Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Header ── */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }

    /* ── Sidebar candidate card ── */
    .candidate-card {
        background: linear-gradient(145deg, #1e1e2e, #2a2a3e);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        color: #e0e0e0;
    }
    .candidate-card h3 {
        color: #667eea;
        margin-top: 0;
        font-size: 1.1rem;
    }
    .card-field {
        display: flex;
        justify-content: space-between;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 0.88rem;
    }
    .card-field .label {
        color: #999;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.5px;
    }
    .card-field .value {
        color: #fff;
        font-weight: 500;
    }

    /* ── Stage badge ── */
    .stage-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        margin-bottom: 0.8rem;
    }
    .stage-greeting    { background: #2d6a4f; color: #b7e4c7; }
    .stage-info        { background: #1d3557; color: #a8dadc; }
    .stage-tech-decl   { background: #6a040f; color: #ffb3b3; }
    .stage-tech-q      { background: #7b2cbf; color: #e0aaff; }
    .stage-wrapup      { background: #ff6d00; color: #fff3e0; }
    .stage-ended       { background: #495057; color: #dee2e6; }

    /* ── Tech stack pills ── */
    .tech-pill {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.78rem;
        margin: 0.15rem 0.2rem;
        font-weight: 500;
    }

    /* ── LLM status indicator ── */
    .llm-status {
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-size: 0.78rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .llm-online  { background: #1b4332; color: #95d5b2; border: 1px solid #2d6a4f; }
    .llm-offline { background: #3d0000; color: #ff8a80; border: 1px solid #6a040f; }

    /* ── Chat area polish ── */
    .stChatMessage {
        border-radius: 12px !important;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Session state initialisation

if "sm" not in st.session_state:
    st.session_state.sm = StateMachine()
    st.session_state.display_messages = []
    st.session_state.session_saved = False

sm: StateMachine = st.session_state.sm


# Sidebar — live candidate card

with st.sidebar:
    st.markdown("## 🎯 TalentScout")

    # LLM status
    if is_llm_available():
        st.markdown('<div class="llm-status llm-online">🟢 LLM Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="llm-status llm-offline">🔴 Offline Mode (no API key)</div>', unsafe_allow_html=True)

    # Stage badge
    stage_map = {
        ConversationState.GREETING: ("🟢 Greeting", "stage-greeting"),
        ConversationState.INFO_GATHERING: ("📝 Info Gathering", "stage-info"),
        ConversationState.TECH_DECLARATION: ("🛠️ Tech Declaration", "stage-tech-decl"),
        ConversationState.TECH_QUESTIONING: ("❓ Tech Questions", "stage-tech-q"),
        ConversationState.WRAP_UP: ("🏁 Wrap Up", "stage-wrapup"),
        ConversationState.ENDED: ("✅ Ended", "stage-ended"),
    }
    label, css_class = stage_map[sm.state]
    st.markdown(f'<div class="stage-badge {css_class}">{label}</div>', unsafe_allow_html=True)

    # Progress bar
    collected, total = sm.get_progress()
    st.progress(collected / total, text=f"Info gathered: {collected}/{total}")

    # Candidate card
    c = sm.candidate
    card_html = '<div class="candidate-card"><h3>📋 Candidate Profile</h3>'

    fields = [
        ("Name", c.name),
        ("Email", mask_email(c.email) if c.email else None),
        ("Phone", mask_phone(c.phone) if c.phone else None),
        ("Location", c.location),
        ("Experience", c.experience),
        ("Position", c.position),
    ]

    for label, value in fields:
        display = value or "—"
        icon = "✅" if value else "⏳"
        card_html += f'''
        <div class="card-field">
            <span class="label">{icon} {label}</span>
            <span class="value">{display}</span>
        </div>'''

    card_html += "</div>"
    st.markdown(card_html, unsafe_allow_html=True)

    # Tech stack pills
    if c.tech_stack:
        st.markdown("**Tech Stack**")
        pills_html = "".join(f'<span class="tech-pill">{t}</span>' for t in c.tech_stack)
        st.markdown(pills_html, unsafe_allow_html=True)

    # Question progress (during tech questioning)
    if sm.state == ConversationState.TECH_QUESTIONING and sm.question_queue:
        answered = max(0, sm.current_question_index - 1)
        total_q = len(sm.question_queue)
        st.markdown("---")
        st.markdown(f"**Questions:** {answered}/{total_q} answered")
        st.progress(answered / total_q)

    # Save session button (available after wrap-up)
    if sm.state == ConversationState.ENDED and not st.session_state.session_saved:
        st.markdown("---")
        if st.button("💾 Save Session", use_container_width=True):
            session_id = hash_session_id(
                c.email or "unknown",
                datetime.now().isoformat(),
            )
            session_data = {
                "candidate": c.model_dump(),
                "tech_answers": sm.tech_answers,
                "messages": sm.context.get_display_messages(),
                "timestamp": datetime.now().isoformat(),
            }
            save_session(session_data, session_id)
            st.session_state.session_saved = True
            st.success(f"Session saved! ID: `{session_id[:12]}…`")

    if st.session_state.session_saved:
        st.success("✅ Session saved")


# Main area — chat interface

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 TalentScout Hiring Assistant</h1>
    <p>AI-powered initial screening for tech candidates</p>
</div>
""", unsafe_allow_html=True)

# Send the greeting on first load
if not sm._greeting_sent:
    greeting = sm.get_greeting()
    st.session_state.display_messages.append({"role": "assistant", "content": greeting})

# Render chat history
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if sm.state != ConversationState.ENDED:
    user_input = st.chat_input("Type your message…")
else:
    user_input = st.chat_input("Session ended — refresh to start a new screening", disabled=True)

if user_input:
    # Show user message immediately
    st.session_state.display_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get bot reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            reply = sm.handle_user_message(user_input)
        st.markdown(reply)

    st.session_state.display_messages.append({"role": "assistant", "content": reply})

    # Rerun to refresh sidebar
    st.rerun()
