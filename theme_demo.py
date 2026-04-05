"""
Theme Demo for PAGie - Shows Different Color Themes
==================================================

Quick demo to show how easy it is to switch themes in the modular UI structure.
"""

from dotenv import load_dotenv
from ui import init_page_config, apply_custom_styles
from ui.styles.themes import get_theme_colors
import streamlit as st

load_dotenv()

def main():
    """Demo different themes for PAGie."""
    init_page_config()
    
    # Create header with custom icon
    header_col1, header_col2 = st.columns([1, 15])
    
    with header_col1:
        st.image("./assets/icon/PAGie_profile_64px.ico", width=60)
    
    with header_col2:
        st.title("🎨 PAGie Theme Demo")
        
    st.caption("See how easy it is to customize the UI with different themes!")
    
    # Theme selector
    theme_options = {
        "Professional Blue": "blue",
        "Nature Green": "green", 
        "Creative Purple": "purple",
        "Elegant Dark": "dark"
    }
    
    selected_theme_name = st.selectbox(
        "Choose a theme:",
        options=list(theme_options.keys()),
        index=0
    )
    
    selected_theme = theme_options[selected_theme_name]
    
    # Apply the selected theme
    apply_custom_styles(theme=selected_theme)
    
    # Show theme colors
    colors = get_theme_colors(selected_theme)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: {colors['primary']}; color: white; padding: 10px; border-radius: 5px; text-align: center;">
            <strong>Primary Color</strong><br>
            {colors['primary']}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: {colors['secondary']}; color: {colors['primary']}; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid {colors['border']};">
            <strong>Secondary Color</strong><br>
            {colors['secondary']}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background-color: white; color: {colors['primary']}; padding: 10px; border-radius: 5px; text-align: center; border: 2px solid {colors['border']};">
            <strong>Border Color</strong><br>
            {colors['border']}
        </div>
        """, unsafe_allow_html=True)
    
    # Demo source badges with current theme
    st.markdown("### Sample Source Badges:")
    badges_html = f"""
    <span class="source-badge">📄 john_doe_cv.pdf</span>
    <span class="source-badge">📄 jane_smith_cv.pdf</span>
    <span class="source-badge">📄 alex_johnson_cv.pdf</span>
    """
    st.markdown(badges_html, unsafe_allow_html=True)
    
    st.markdown("### How to Apply This Theme:")
    st.code(f"""
# In app_modular.py, change this line:
apply_custom_styles(theme='{selected_theme}')

# That's it! The entire UI will use the new theme.
""", language="python")

if __name__ == "__main__":
    main()