"""
UI Module for PAGie - Personal AI Generation & Information Engine
================================================================

This module contains all the Streamlit UI components, styling, and configuration
for the PAGie chat interface. This separation allows for better UI design focus
and maintainability.

Components:
- sidebar: System status, actions, and EDA report viewer
- chat_interface: Main conversational chat UI
- source_badges: Source citation display components

Styles:
- main.css: Core CSS styling for the application
- themes: Color themes and design variables

Usage:
    from ui import init_page_config, render_sidebar, render_chat_interface
"""

from .config import init_page_config
from .components.sidebar import render_sidebar
from .components.chat_interface import render_chat_interface
from .components.file_explorer import render_file_viewer
from .styles.themes import apply_custom_styles

__all__ = [
    "init_page_config",
    "render_sidebar", 
    "render_chat_interface",
    "render_file_viewer",
    "apply_custom_styles"
]