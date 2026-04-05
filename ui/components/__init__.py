"""
UI Components for PAGie
=======================

Reusable Streamlit components for the PAGie chat interface.
"""

from .sidebar import render_sidebar
from .chat_interface import render_chat_interface
from .source_badges import render_source_badges
from .file_explorer import render_file_explorer, render_file_viewer, get_cv_files_summary

__all__ = ["render_sidebar", "render_chat_interface", "render_source_badges", "render_file_explorer", "render_file_viewer", "get_cv_files_summary"]