#!/bin/bash
# run_local.sh - Quick start script for local PAGie development

echo "🏠 Starting PAGie in LOCAL MODE..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Features:"
echo "  ✅ Google Drive OAuth sync"
echo "  ✅ Local ChromaDB (./chroma_db)"
echo "  ✅ Ollama support (if enabled)"
echo "  ✅ Local cache and assets"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "✅ .env created! Please edit it with your API keys:"
    echo "   nano .env"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

# Check if venv exists
if [ ! -d venv ]; then
    echo "⚠️  Virtual environment not found!"
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Virtual environment created and dependencies installed!"
else
    source venv/bin/activate
fi

echo ""
echo "🚀 Launching app_local.py..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

streamlit run app_local.py
