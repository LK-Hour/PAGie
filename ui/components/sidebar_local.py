"""
Sidebar Component for PAGie (Local-Only Version)
================================================

Local-only sidebar with NO cloud detection or GCS sync.
This version uses pure local paths and Google Drive OAuth.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..config import UIConfig
from ..styles.themes import ColorTheme
from .file_explorer import render_file_explorer

def render_sidebar_local() -> None:
    """Render the complete sidebar (local-only mode)."""
    
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
    """Render sidebar header with compact logo."""
    st.markdown(f"""
        <div style="
            text-align: center;
        ">
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            ">
                <img src="data:image/png;base64,{_get_profile_logo_base64()}" 
                     style="width: 240px; height: auto; margin-bottom: 0.5rem;">
                <h2 style="
                    margin: 0;
                    color: {ColorTheme.PRIMARY_COLOR};
                    font-size: 1.4rem;
                    font-weight: 700;
                    letter-spacing: 0.02em;
                ">PAGie</h2>
            </div>
            <p style="
                margin: 0.25rem 0 0 0;
                color: #94a3b8;
                font-size: 0.75rem;
                font-weight: 400;
            ">Second Brain AI</p>
            <p style="
                margin: 0;
                color: #64748b;
                font-size: 0.7rem;
                font-weight: 600;
            ">CADT · Group 5 · LOCAL MODE</p>
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

def _render_system_status() -> None:
    """Render system status section."""
    st.markdown("#### :material/router: System")
    
    try:
        # Import here to avoid circular imports
        from rag_pipeline import get_cache_stats, get_db_stats
        
        stats = get_db_stats()
        is_connected = "Connected" in stats.get("status", "")
        status_icon = ":material/check_circle:" if is_connected else ":material/error:"
        
        # Simple status display
        st.markdown(f"{status_icon} **Vector DB:** {stats.get('status', 'Unknown')}")
        st.caption(f"Mode: {stats.get('app_mode', 'unknown')} · {stats.get('llm_model', 'n/a')}")
        
        # Metrics in compact layout
        col1, col2 = st.columns(2)
        col1.metric("Chunks", stats.get("total_chunks", "N/A"))
        
        cache_stats = get_cache_stats()
        hit_rate = cache_stats.get("hit_rate", 0) * 100
        col2.metric("Cache", f"{hit_rate:.0f}%")
        
    except Exception as e:
        st.error(f"DB Error: {str(e)[:30]}...")
        col1, col2 = st.columns(2)
        col1.metric("Chunks", "N/A")
        col2.metric("Cache", "N/A")

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
    
    st.metric("Last Sync", sync_text, help="Most recent Google Drive sync")

def _render_action_buttons() -> None:
    """Render action buttons section (local-only)."""
    st.markdown("#### :material/settings: Actions")

    # Sync CV Files button (Google Drive OAuth only)
    if st.button(":material/sync: Sync from Drive", 
                 use_container_width=True, 
                 help="Sync CV files from Google Drive (OAuth)"):
        with st.spinner("Syncing from Google Drive..."):
            try:
                from sync_data import run_sync
                run_sync()
                
                # Count synced files
                cv_dir = Path("./data/drive")
                file_count = len(list(cv_dir.glob("*.pdf")))
                
                st.success(f"✅ Synced {file_count} CV files from Google Drive")
                st.rerun()
            except Exception as e:
                st.error(f"Sync error: {e}")

    # Rebuild Knowledge Base button (local paths only)
    if st.button(":material/science: Rebuild KB", 
                 use_container_width=True, 
                 help="Re-process CV files and rebuild ChromaDB"):
        with st.spinner("Processing CVs and building ChromaDB..."):
            try:
                from data_science_eda import run_pipeline
                import rag_pipeline
                
                # First explicitly free the Database connection 
                # so data_science_eda.py can safely delete and recreate it.
                rag_pipeline._vector_db_instance = None
                
                df, _ = run_pipeline()
                if df is not None:
                    st.success(f"✅ Done! Processed {len(df)} text chunks.")
                    st.rerun()
                else:
                    st.warning("⚠️ No files found. Sync from Drive first.")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

    # Clear Chat History button
    if st.button(":material/delete: Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

def _render_eda_report() -> None:
    """Render EDA report viewer section."""
    st.markdown("#### :material/analytics: EDA Report")
    eda_path = Path("./assets/eda_report.png")
    
    if eda_path.exists():
        st.image(
            str(eda_path),
            use_container_width=True,
            caption="IQR filtering analysis",
        )
        # Show when the EDA was last generated
        import os
        mtime = os.path.getmtime(eda_path)
        st.caption(f"Generated: {datetime.fromtimestamp(mtime).strftime('%b %d, %H:%M')}")
    else:
        st.info("📊 No EDA report yet. Click 'Rebuild KB' to generate.")

    st.divider()

def _render_footer() -> None:
    """Render sidebar footer."""
    st.caption(UIConfig.FOOTER_TEXT)
