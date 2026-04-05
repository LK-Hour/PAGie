"""
Source Citation Components
=========================

Components for displaying source citations and badges.
"""

import streamlit as st
from pathlib import Path
from typing import List

def render_source_badges(sources: List[str]) -> None:
    """
    Render source citation badges below chat messages.
    
    DISABLED per user request - sources are no longer displayed.
    
    Args:
        sources: List of source file paths/names
    """
    # Source display disabled - return immediately
    return
    
    # Original code commented out:
    # if not sources:
    #     return
    #     
    # # Remove duplicates while preserving order
    # unique_sources = list(dict.fromkeys(sources))
    # 
    # badges_html = "".join([
    #     f'<span class="source-badge">{Path(s).name}</span>'
    #     for s in unique_sources
    # ])
    # 
    # st.markdown(
    #     f"<small><b>Sources:</b></small><br>{badges_html}",
    #     unsafe_allow_html=True,
    # )

def render_source_summary(sources: List[str]) -> None:
    """
    Render a summary of sources used in the session.
    
    Args:
        sources: List of all source files used
    """
    if not sources:
        st.info("No sources referenced yet.")
        return
        
    unique_sources = list(set(sources))
    
    st.markdown("### Sources Used This Session")
    for source in unique_sources:
        st.markdown(f"- {Path(source).name}")

def create_source_badge_html(source: str, include_icon: bool = True) -> str:
    """
    Create HTML for a single source badge.
    
    Args:
        source: Source file path/name
        include_icon: Whether to include file icon
        
    Returns:
        HTML string for the badge
    """
    icon = "" if include_icon else ""
    filename = Path(source).name
    
    return f'<span class="source-badge">{icon}{filename}</span>'