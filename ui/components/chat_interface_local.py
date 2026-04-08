"""
Chat Interface Component for PAGie (Local Version)
=================================================

Main conversational chat UI with message rendering and input handling.
This version uses rag_pipeline_local for local development.
"""

import streamlit as st
from typing import Dict, Any, List

from ..config import UIConfig
from ..styles.themes import ColorTheme
from .source_badges import render_source_badges
from .file_explorer import render_file_viewer

def render_chat_interface() -> None:
    """Render the complete chat interface."""
    
    # Check if file viewer should be shown
    if st.session_state.get('show_file_viewer', False):
        render_file_viewer()
    else:
        _render_header()
        _initialize_session_state()
        _render_chat_history()
        _handle_user_input()

def _render_header() -> None:
    """Render chat interface header with clean, modern design."""
    col1, col2 = st.columns([1, 20])
    
    with col1:
        st.image(UIConfig.APP_ICON_PATH, width=60)
    
    with col2:
        st.markdown(f"""
            <div style="padding-top: 0.5rem;">
                <h1 style="
                    margin: 0 0 0.5rem 0;
                    padding: 0;
                    font-size: 2rem;
                    font-weight: 700;
                    color: {ColorTheme.PRIMARY_COLOR};
                ">PAGie — Your Second Brain</h1>
                <p style="
                    margin: 0;
                    font-size: 0.95rem;
                    color: {ColorTheme.TEXT_SECONDARY};
                ">Personal AI Generation & Information Engine powered by Gemini (Local Mode).</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f'<p style="color: {ColorTheme.TEXT_SECONDARY}; font-size: 0.95rem;">{UIConfig.APP_DESCRIPTION}</p>', unsafe_allow_html=True)

def _initialize_session_state() -> None:
    """Initialize chat session state if not exists."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": UIConfig.WELCOME_MESSAGE,
                "sources": [],
            }
        ]

def _render_chat_history() -> None:
    """Render all messages in chat history."""
    for message in st.session_state.messages:
        avatar = UIConfig.ASSISTANT_AVATAR if message["role"] == "assistant" else UIConfig.USER_AVATAR
        
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            
            # Render source badges for assistant messages
            if message["role"] == "assistant" and message.get("sources"):
                render_source_badges(message["sources"])

def _handle_user_input() -> None:
    """Handle user input and generate responses."""
    if prompt := st.chat_input(UIConfig.CHAT_INPUT_PLACEHOLDER):
        # Add user message to history
        _add_user_message(prompt)
        
        # Generate and display assistant response
        _generate_assistant_response(prompt)

def _add_user_message(content: str) -> None:
    """Add user message to session state and display it."""
    st.session_state.messages.append({
        "role": "user", 
        "content": content, 
        "sources": []
    })
    
    with st.chat_message("user", avatar=UIConfig.USER_AVATAR):
        st.markdown(content)

def _generate_assistant_response(query: str) -> None:
    """Generate and display assistant response (using local pipeline)."""
    with st.chat_message("assistant", avatar=UIConfig.ASSISTANT_AVATAR):
        with st.spinner("Thinking..."):
            # Import local pipeline for local development
            from rag_pipeline_local import query_pagie
            result = query_pagie(query)

        answer_text = _to_display_text(result.get("answer", ""))
        st.markdown(answer_text)

        # Render source badges
        if result.get("sources"):
            render_source_badges(result["sources"])

    # Add assistant response to session history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "sources": result.get("sources", []),
    })

def _to_display_text(value) -> str:
    """Convert mixed model payloads into clean text for Streamlit markdown."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            elif hasattr(item, "text") and getattr(item, "text"):
                parts.append(str(getattr(item, "text")))
        if parts:
            return "\n\n".join(parts)
    return str(value)

def render_chat_statistics() -> Dict[str, Any]:
    """Render chat session statistics (optional feature)."""
    if "messages" not in st.session_state:
        return {}
    
    messages = st.session_state.messages
    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    
    # Collect all sources used in session
    all_sources = []
    for msg in assistant_messages:
        all_sources.extend(msg.get("sources", []))
    
    unique_sources = list(set(all_sources))
    
    stats = {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "sources_referenced": len(unique_sources),
        "unique_sources": unique_sources
    }
    
    return stats
