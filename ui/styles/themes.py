"""
Theme and Styling for PAGie UI
==============================

Contains CSS styles, color themes, and design customization options.
"""

import streamlit as st

class ColorTheme:
    """Color theme configuration for easy customization."""
    
    # PAGie Modern Theme - Consistent indigo/purple design
    PRIMARY_COLOR = "#6366f1"      # Vibrant indigo
    PRIMARY_DARK = "#4338ca"       # Deep indigo
    ACCENT_COLOR = "#8b5cf6"       # Purple accent (consistent with gradient)
    SECONDARY_COLOR = "#f0f9ff"    # Light blue
    BORDER_COLOR = "#e0e7ff"       # Soft indigo border
    BACKGROUND_COLOR = "#fafbff"   # Very light blue-white
    
    # Text colors
    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    
    # Status colors (using consistent blue/purple tones)
    SUCCESS_COLOR = "#10b981"      # Green (keep for success)
    WARNING_COLOR = "#a78bfa"      # Light purple (instead of orange)
    ERROR_COLOR = "#6366f1"        # Indigo (instead of red)
    INFO_COLOR = "#3b82f6"         # Blue
    
    # Gradient presets (consistent indigo/purple theme)
    GRADIENT_PRIMARY = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)"
    GRADIENT_ACCENT = "linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)"
    GRADIENT_SOFT = "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)"
    GRADIENT_HEADER = "linear-gradient(120deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)"
    
    # Alternative themes (easily switchable)
    THEMES = {
        "modern": {
            "primary": "#6366f1",
            "primary_dark": "#4338ca",
            "accent": "#8b5cf6",
            "secondary": "#f0f9ff", 
            "border": "#e0e7ff",
            "gradient": "linear-gradient(120deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)"
        },
        "ocean": {
            "primary": "#0ea5e9",
            "primary_dark": "#0284c7",
            "accent": "#06b6d4",
            "secondary": "#f0f9ff",
            "border": "#bae6fd",
            "gradient": "linear-gradient(120deg, #0ea5e9 0%, #06b6d4 50%, #2dd4bf 100%)"
        },
        "sunset": {
            "primary": "#f59e0b",
            "primary_dark": "#d97706",
            "accent": "#fbbf24",
            "secondary": "#fef3c7",
            "border": "#fde68a",
            "gradient": "linear-gradient(120deg, #f59e0b 0%, #fbbf24 50%, #fcd34d 100%)"
        },
        "forest": {
            "primary": "#059669",
            "primary_dark": "#047857",
            "accent": "#10b981",
            "secondary": "#ecfdf5",
            "border": "#a7f3d0",
            "gradient": "linear-gradient(120deg, #059669 0%, #10b981 50%, #34d399 100%)"
        }
    }

def get_theme_colors(theme_name: str = "modern") -> dict:
    """Get color palette for specified theme."""
    return ColorTheme.THEMES.get(theme_name, ColorTheme.THEMES["modern"])

def apply_custom_styles(theme: str = "modern"):
    """Apply custom CSS styles to the Streamlit app with clean, working design."""
    
    colors = get_theme_colors(theme)
    
    css = f"""
    <style>
        /* Import Google Fonts for better typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Global typography */
        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Main title styling - solid color that works in dark mode */
        h1 {{
            color: {colors['primary']} !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}
        
        h2 {{
            color: {colors['primary']} !important;
            font-weight: 600 !important;
        }}
        
        /* Chat message styling */
        .stChatMessage {{
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }}
        
        /* User message with gradient background */
        .stChatMessage[data-testid*="user"] {{
            background: linear-gradient(135deg, {colors['primary']} 0%, {colors['primary_dark']} 100%);
            border: none;
        }}
        
        .stChatMessage[data-testid*="user"] p,
        .stChatMessage[data-testid*="user"] * {{
            color: white !important;
        }}
        
        /* Assistant message with border */
        .stChatMessage[data-testid*="assistant"] {{
            border-left: 4px solid {colors['primary']};
        }}
        
        /* Source badges with clean design */
        .source-badge {{
            display: inline-block;
            background-color: {colors['primary']};
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            margin: 4px 4px 4px 0;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .source-badge:hover {{
            background-color: {colors['primary_dark']};
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
        }}
        
        /* Button styling */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 600;
            background: {colors['primary']};
            color: white;
            border: none;
            transition: all 0.2s ease;
        }}
        
        .stButton > button:hover {{
            background: {colors['primary_dark']};
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }}
        
        /* Metrics styling */
        [data-testid="stMetricValue"] {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {colors['primary']};
        }}
        
        /* Chat input */
        .stChatInputContainer {{
            border-radius: 12px;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
            color: {ColorTheme.TEXT_SECONDARY} !important;
        }}
        
        /* Tab hover state - use indigo instead of red */
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {colors['secondary']} !important;
            color: {colors['primary']} !important;
        }}
        
        /* Selected tab - indigo background */
        .stTabs [aria-selected="true"] {{
            background-color: {colors['primary']} !important;
            color: white !important;
            border-bottom: 2px solid {colors['primary']} !important;
        }}
        
        /* Remove any red underlines from tabs */
        .stTabs [data-baseweb="tab-highlight"] {{
            background-color: {colors['primary']} !important;
        }}
        
        /* Text input focus state - use indigo instead of red */
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stChatInput > div > div > input:focus {{
            border-color: {colors['primary']} !important;
            box-shadow: 0 0 0 1px {colors['primary']} !important;
        }}
        
        /* Chat input - no borders at all */
        .stChatInput > div,
        .stChatInput > div > div,
        .stChatInput textarea,
        .stChatInput input,
        .stChatInputContainer,
        .stChatInputContainer > div,
        .stChatInputContainer textarea,
        .stChatInputContainer input {{
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }}
        
        .stChatInput textarea:focus,
        .stChatInput input:focus,
        .stChatInputContainer textarea:focus,
        .stChatInputContainer input:focus {{
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }}
        
        /* Override all Streamlit default red focus states */
        input:focus,
        textarea:focus,
        select:focus {{
            outline-color: {colors['primary']} !important;
            border-color: {colors['primary']} !important;
        }}
        
        /* Universal focus override - only outline color, no extra borders */
        *:focus-visible {{
            outline-color: {colors['primary']} !important;
            outline-width: 2px !important;
            outline-offset: 2px !important;
        }}
        
        /* Override any remaining red borders in text inputs */
        [data-baseweb="input"]:focus-within,
        [data-baseweb="base-input"]:focus-within,
        [data-baseweb="textarea"]:focus-within {{
            border-color: {colors['primary']} !important;
            box-shadow: 0 0 0 1px {colors['primary']} !important;
        }}
        
        /* Tab panel border color */
        [data-baseweb="tab-panel"] {{
            border-top-color: {colors['primary']} !important;
        }}
        
        /* Dividers */
        hr {{
            margin: 1rem 0;
        }}
        
        /* Success/Error/Warning messages */
        .stSuccess {{
            background-color: rgba(16, 185, 129, 0.1);
            border-left: 4px solid {ColorTheme.SUCCESS_COLOR};
            border-radius: 4px;
            padding: 1rem;
        }}
        
        .stError {{
            background-color: rgba(239, 68, 68, 0.1);
            border-left: 4px solid {ColorTheme.ERROR_COLOR};
            border-radius: 4px;
            padding: 1rem;
        }}
        
        .stWarning {{
            background-color: rgba(245, 158, 11, 0.1);
            border-left: 4px solid {ColorTheme.WARNING_COLOR};
            border-radius: 4px;
            padding: 1rem;
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            border-radius: 8px;
            font-weight: 500;
        }}
        
        /* Download button */
        .stDownloadButton > button {{
            border: 2px solid {colors['primary']};
            background: transparent;
            color: {colors['primary']};
            border-radius: 8px;
            font-weight: 500;
        }}
        
        .stDownloadButton > button:hover {{
            background: {colors['primary']};
            color: white;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {colors['primary']};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {colors['primary_dark']};
        }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)