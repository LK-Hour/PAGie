"""
Sidebar Component for PAGie
===========================

Contains system status, action buttons, and EDA report viewer.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..config import UIConfig
from ..styles.themes import ColorTheme
from .file_explorer import render_file_explorer

def render_sidebar() -> None:
    """Render the complete sidebar with all sections."""
    
    with st.sidebar:
        _render_header()
        
        # Create tabs for different sidebar sections
        tab1, tab2 = st.tabs([":material/settings: System", ":material/folder: Files"])
        
        with tab1:
            _render_system_status()
            _render_action_buttons()
            _render_eda_report()
        
        with tab2:
            render_file_explorer()
        
        _render_footer()

def _render_header() -> None:
    """Render sidebar header with high-quality logo."""
    st.markdown(f"""
        <div style="
            padding: 0rem 0.5rem 1rem 0rem;
            text-align: center;
        ">
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            ">
                <img src="data:image/png;base64,{_get_profile_logo_base64()}" 
                     style="width: 480px; height: auto;">
                <h2 style="
                    margin: 0;
                    color: {ColorTheme.PRIMARY_COLOR};
                    font-size: 1.8rem;
                    font-weight: 700;
                    letter-spacing: 0.02em;
                ">PAGie</h2>
            </div>
            <p style="
                margin: 0 0 0.5rem 0;
                color: #94a3b8;
                font-size: 0.85rem;
                font-weight: 400;
            ">Second Brain AI</p>
            <p style="
                margin: 0;
                color: #64748b;
                font-size: 0.75rem;
                font-weight: 800;
            ">CADT · Group 5 · Data Science Project</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

def _get_profile_logo_base64() -> str:
    """Get base64 encoded high-quality profile logo."""
    import base64
    from pathlib import Path
    
    # Use the high-quality profile PNG
    logo_path = Path("./assets/PAGie_profile_transparent.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    # Fallback to icon if profile not found
    icon_path = Path(UIConfig.APP_ICON_PATH)
    if icon_path.exists():
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def _get_icon_base64() -> str:
    """Get base64 encoded icon for embedding in HTML."""
    import base64
    from pathlib import Path
    
    icon_path = Path(UIConfig.APP_ICON_PATH)
    if icon_path.exists():
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def _render_system_status() -> None:
    """Render system status section with clean card design."""
    st.markdown("### :material/router: System Status")
    
    try:
        # Import here to avoid circular imports
        from rag_pipeline import get_cache_stats
        try:
            from rag_pipeline import get_db_stats
        except (ImportError, AttributeError):
            def get_db_stats():
                return {"status": "Connected", "total_chunks": "N/A", "app_mode": "prod"}
        
        stats = get_db_stats()
        is_connected = "Connected" in stats.get("status", "")
        status_icon = ":material/check_circle:" if is_connected else ":material/error:"
        
        # Simple status display
        st.markdown(f"{status_icon} **Vector DB:** {stats.get('status', 'Unknown')}")
        st.caption(f"Mode: {stats.get('app_mode', 'unknown')} · LLM: {stats.get('llm_provider', 'n/a')} ({stats.get('llm_model', 'n/a')})")
        
        # Metrics
        col1, col2 = st.columns(2)
        col1.metric("Chunks", stats.get("total_chunks", "N/A"), help="Total text chunks in vector database")
        
        cache_stats = get_cache_stats()
        hit_rate = cache_stats.get("hit_rate", 0) * 100
        col2.metric("Cache Hit", f"{hit_rate:.1f}%", help="Embedding cache performance")
        
    except Exception as e:
        st.error(f"Error connecting to Vector DB: {str(e)[:50]}")
        col1, col2 = st.columns(2)
        col1.metric("Chunks", "N/A")
        col2.metric("Cache Hit", "N/A")

    # Display last sync timestamp
    _render_sync_status()
    st.divider()

def _render_sync_status() -> None:
    """Render last sync timestamp."""
    last_sync_path = Path("./data/last_sync.txt")
    
    if last_sync_path.exists():
        with open(last_sync_path, "r") as f:
            raw_ts = f.read().strip()
        try:
            dt = datetime.fromisoformat(raw_ts)
            sync_text = dt.strftime("%b %d, %H:%M")
        except ValueError:
            sync_text = raw_ts[:16]
    else:
        sync_text = "Never"
    
    st.metric("Last Sync", sync_text, help="Most recent data synchronization")

def _render_action_buttons() -> None:
    """Render action buttons section."""
    st.markdown("### :material/settings: Actions")

    # Sync CV Files button
    if st.button(":material/sync: Sync CV Files", 
                 use_container_width=True, 
                 help="Fetch latest CV files from Google Drive folder"):
        with st.spinner("Connecting to Google Drive..."):
            try:
                from sync_data import run_sync
                run_sync()
                st.success("Sync complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Sync failed: {e}")

    # Rebuild Knowledge Base button
    if st.button(":material/science: Rebuild Knowledge Base", 
                 use_container_width=True, 
                 help="Re-process CV files: chunk → IQR filter → embed → store"):
        with st.spinner("Running Data Science pipeline (this may take a minute)..."):
            try:
                from data_science_eda import run_pipeline
                df, _ = run_pipeline()
                if df is not None:
                    st.success(f"Done! {len(df)} clean CV chunks indexed.")
                    st.rerun()
                else:
                    st.warning("No CV files found. Sync first.")
            except Exception as e:
                st.error(f"Pipeline failed: {e}")

    # Clear Chat History button
    if st.button(":material/delete: Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

def _render_eda_report() -> None:
    """Render EDA report viewer section."""
    st.markdown("### :material/analytics: EDA Report")
    eda_path = Path("./assets/eda_report.png")
    
    if eda_path.exists():
        st.image(
            str(eda_path),
            use_container_width=True,
            caption="Latest IQR filtering & data distribution analysis",
        )
        # Show when the EDA was last generated
        import os
        mtime = os.path.getmtime(eda_path)
        st.caption(f"Generated: {datetime.fromtimestamp(mtime).strftime('%b %d %Y, %H:%M')}")
    else:
        st.info("No EDA report yet.\nClick 'Rebuild Knowledge Base' to generate one.")

    st.divider()

def _render_footer() -> None:
    """Render sidebar footer."""
    st.caption(UIConfig.FOOTER_TEXT)