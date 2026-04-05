"""
Page Configuration for PAGie Streamlit App
==========================================

Contains page settings, constants, and initialization logic.
"""

import streamlit as st
from .styles.themes import ColorTheme

def init_page_config():
    """Initialize Streamlit page configuration with custom theme."""
    st.set_page_config(
        page_title="PAGie — Your Second Brain AI",
        page_icon="./assets/icon/PAGie_profile_64px.ico",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "PAGie - Personal AI Generation & Information Engine"
        }
    )
    
    # Inject custom theme colors via CSS (Streamlit's theme parameter is limited)
    st.markdown(f"""
        <style>
            /* Override Streamlit's default theme colors */
            :root {{
                --primary-color: {ColorTheme.PRIMARY_COLOR};
                --background-color: {ColorTheme.BACKGROUND_COLOR};
                --secondary-background-color: {ColorTheme.SECONDARY_COLOR};
                --text-color: {ColorTheme.TEXT_PRIMARY};
            }}
        </style>
    """, unsafe_allow_html=True)

# UI Constants
class UIConfig:
    """UI configuration constants."""
    
    # App Information  
    APP_TITLE = "PAGie — CV Analysis & Candidate Information System"
    APP_SUBTITLE = "Personal AI Generation & Information Engine"
    APP_ICON_PATH = "./assets/icon/PAGie_profile_64px.ico"
    APP_DESCRIPTION = (
        "Ask me anything about the candidates in your CV database. "
        "I analyze resumes and provide accurate information based on the CV files."
    )
    
    # Branding
    PROJECT_INFO = "CADT · Group 5 · Data Science Project"
    FOOTER_TEXT = "Built with LangChain · ChromaDB · Gemini · Streamlit"
    
    # Chat Configuration
    CHAT_INPUT_PLACEHOLDER = "Ask about candidates... e.g. 'Who has Python experience?'"
    USER_AVATAR = "👤"
    ASSISTANT_AVATAR = "./assets/icon/PAGie_profile_64px.ico"
    
    # Welcome Message
    WELCOME_MESSAGE = (
        "👋 Hi! I'm **PAGie**, speaking as your knowledge-backed version of you.\n\n"
        "When I answer, I'll respond in **first person** using your synced notes, "
        "documents, and project materials. Ask me things like interview questions, "
        "project updates, academic background, or anything stored in your knowledge base.\n\n"
        "*What would you like me to answer as you today?*"
    )