#!/bin/bash
# Quick start script for PAGie with the new modern UI

echo "Starting PAGie - Your Second Brain AI"
echo "=========================================="
echo ""
echo "✨ New Modern UI Features:"
echo "  • Gradient-based design system"
echo "  • Glassmorphism effects"
echo "  • Smooth animations"
echo "  • Professional typography"
echo "  • Multiple color themes"
echo ""
echo "🎨 Available themes: modern, ocean, sunset, forest"
echo "   (Change in app_modular.py, line 46)"
echo ""
echo "Starting app on http://localhost:8501"
echo "=========================================="
echo ""

# Activate virtual environment and run Streamlit
source venv/bin/activate
streamlit run app_modular.py
