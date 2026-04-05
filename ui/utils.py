"""
UI Utilities for PAGie
======================

Helper functions for UI components and theme management.
"""

import streamlit as st
from typing import Dict, Any, List
from pathlib import Path

def get_session_stats() -> Dict[str, Any]:
    """Get statistics about the current chat session."""
    if "messages" not in st.session_state:
        return {"total_messages": 0, "sources_used": 0}
    
    messages = st.session_state.messages
    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    
    # Collect all sources
    all_sources = []
    for msg in assistant_messages:
        all_sources.extend(msg.get("sources", []))
    
    unique_sources = list(set(all_sources))
    
    return {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "sources_used": len(unique_sources),
        "unique_sources": unique_sources
    }

def clear_chat_history() -> None:
    """Clear the chat history and reset to welcome message."""
    from .config import UIConfig
    
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": UIConfig.WELCOME_MESSAGE,
            "sources": [],
        }
    ]

def export_chat_history() -> str:
    """Export chat history to markdown format."""
    if "messages" not in st.session_state:
        return "No chat history to export."
    
    markdown_content = "# PAGie Chat History\n\n"
    
    for i, message in enumerate(st.session_state.messages):
        role = "**User:**" if message["role"] == "user" else "**PAGie:**"
        content = message["content"]
        sources = message.get("sources", [])
        
        markdown_content += f"{role}\n{content}\n"
        
        if sources:
            markdown_content += f"\n*Sources: {', '.join([Path(s).name for s in sources])}*\n"
        
        markdown_content += "\n---\n\n"
    
    return markdown_content

def create_theme_selector() -> str:
    """Create a theme selector widget."""
    theme_options = {
        "Professional Blue": "blue",
        "Nature Green": "green", 
        "Creative Purple": "purple",
        "Elegant Dark": "dark"
    }
    
    selected_theme_name = st.selectbox(
        "Choose Theme",
        options=list(theme_options.keys()),
        index=0,
        help="Select a color theme for the interface"
    )
    
    return theme_options[selected_theme_name]

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def create_download_button(content: str, filename: str, label: str) -> None:
    """Create a download button for text content."""
    st.download_button(
        label=label,
        data=content,
        file_name=filename,
        mime="text/plain",
        use_container_width=True
    )