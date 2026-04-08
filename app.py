"""
app_modular.py — Modular Streamlit Frontend for PAGie
=====================================================

A clean, modular version of the PAGie CV Analysis System interface.
This version separates UI components for better maintainability and design focus.

Features:
  - Modular UI components (sidebar, chat interface, styling)
  - Easy theme customization
  - Reusable components
  - Clean separation of concerns
  - File explorer for viewing CV files

Usage:
  streamlit run app_modular.py
"""

# Environment management - optional for Streamlit Cloud
try:
    from dotenv import load_dotenv
    _dotenv_available = True
except ImportError:
    # On Streamlit Cloud, dotenv is not needed (uses st.secrets instead)
    _dotenv_available = False

# Import modular UI components
from ui import (
    init_page_config,
    apply_custom_styles,
    render_sidebar,
    render_chat_interface
)

# Import backend functionality
from rag_pipeline import warmup_models
import streamlit as st

# Import GCS sync for cloud deployment
from gcs_sync import ensure_chromadb_synced

# Load environment variables (only if dotenv is available)
if _dotenv_available:
    load_dotenv()

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

def initialize_app():
    """Initialize the PAGie application."""
    # Page configuration (must be first Streamlit command)
    init_page_config()
    
    # Apply custom styling with modern theme
    apply_custom_styles(theme="modern")  # Options: modern, ocean, sunset, forest
    
    # Ensure ChromaDB is synced before initialization
    ensure_chromadb_synced()
    
    # Initialize models after ChromaDB is ready
    initialize_pagie()

@st.cache_resource
def initialize_pagie():
    """Initialize and warm up PAGie models (cached for performance)."""
    try:
        warmup_models()
        return True
    except Exception as e:
        st.error(f"Failed to initialize PAGie: {e}")
        return False

# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

def main():
    """Main application entry point."""
    # Initialize app
    initialize_app()
    
    # Render UI components
    render_sidebar()         # System status, actions, EDA report, file explorer
    render_chat_interface()  # Main chat interface or file viewer

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()