"""
app_local.py — Local-Only Streamlit Frontend for PAGie
=====================================================

A clean, local-only version of the PAGie CV Analysis System.
This version is optimized for local development with NO cloud logic.

Features:
  - Pure local development (no cloud detection)
  - Google Drive OAuth sync (sync_data.py)
  - Local ChromaDB (./chroma_db)
  - Local cache and assets
  - Full Ollama support
  - Modular UI components

Usage:
  streamlit run app_local.py
"""

import os

# CRITICAL: Force local mode BEFORE any other imports
# This prevents cloud path detection in rag_pipeline.py and data_science_eda.py
os.environ["FORCE_LOCAL_MODE"] = "true"

from dotenv import load_dotenv

# Import modular UI components
from ui import (
    init_page_config,
    apply_custom_styles
)

# Import local chat interface (uses rag_pipeline_local)
from ui.components.chat_interface_local import render_chat_interface

# Import local sidebar (without cloud logic)
from ui.components.sidebar_local import render_sidebar_local

# Import backend functionality
from rag_pipeline_local import warmup_models
import streamlit as st

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Debug: Print actual paths being used
# ---------------------------------------------------------------------------
print("\n" + "="*70)
print("🏠 PAGie Local Mode - Path Configuration")
print("="*70)

from rag_pipeline_local import CHROMA_DB_PATH, EMBEDDING_CACHE_PATH
from data_science_eda import CHROMA_DB_DIR, ASSETS_DIR

print(f"FORCE_LOCAL_MODE:     {os.environ.get('FORCE_LOCAL_MODE', 'NOT SET')}")
print(f"ChromaDB (rag):       {CHROMA_DB_PATH}")
print(f"ChromaDB (eda):       {CHROMA_DB_DIR}")
print(f"Embedding Cache:      {EMBEDDING_CACHE_PATH}")
print(f"Assets:               {ASSETS_DIR}")

if str(CHROMA_DB_PATH).startswith('/tmp'):
    print("\n⚠️  WARNING: Using /tmp paths! This should be local!")
    print("   If you see this, please report it as a bug.")
else:
    print("\n✅ Using local paths (correct)")

print("="*70 + "\n")

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

def initialize_app():
    """Initialize the PAGie application (local mode)."""
    # Page configuration (must be first Streamlit command)
    init_page_config()
    
    # Apply custom styling with modern theme
    apply_custom_styles(theme="modern")  # Options: modern, ocean, sunset, forest
    
    # Initialize models (cached for performance)
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
    render_sidebar_local()   # Local-only sidebar (no cloud sync)
    render_chat_interface()  # Main chat interface or file viewer

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
