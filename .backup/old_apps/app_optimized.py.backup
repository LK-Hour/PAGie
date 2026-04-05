"""
app_optimized.py — High-Performance Streamlit UI for PAGie
==========================================================
Optimized version with model pre-loading, caching, and faster responses.
"""

import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Use optimized pipeline
from rag_pipeline_optimized import query_pagie_fast, get_db_stats, warmup_models

load_dotenv()

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PAGie — CV Analysis System (Optimized)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# OPTIMIZATION: Model Pre-loading with Session State
# ---------------------------------------------------------------------------
if 'models_warmed' not in st.session_state:
    with st.spinner("🔥 Warming up AI models (one-time setup)..."):
        warmup_models()
        st.session_state.models_warmed = True
        st.session_state.warmup_time = time.time()

# ---------------------------------------------------------------------------
# Initialize Session State
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# ---------------------------------------------------------------------------
# Header Section
# ---------------------------------------------------------------------------
st.title("⚡ PAGie — High-Performance CV Analysis")
st.markdown("*Optimized AI Assistant for Candidate Resume Analysis*")

# Performance indicator
if st.session_state.models_warmed:
    st.success("🚀 **Models Loaded** - Ready for fast queries!")
else:
    st.warning("⏳ Loading models...")

# ---------------------------------------------------------------------------
# Sidebar - System Status & Controls  
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ System Control")
    
    # Performance stats
    if st.button("📊 Refresh Stats"):
        st.rerun()
    
    stats = get_db_stats()
    
    if "error" not in stats:
        st.metric("📄 Total CV Chunks", stats.get("total_chunks", 0))
        st.metric("🧠 Cached Embeddings", stats.get("embedding_cache_size", 0))
        st.metric("💬 Queries This Session", st.session_state.query_count)
        
        # Model status indicators
        models = stats.get("models_loaded", {})
        st.write("**Model Status:**")
        st.write(f"✅ Embeddings: {'Ready' if models.get('embeddings') else 'Loading'}")
        st.write(f"✅ Vector DB: {'Ready' if models.get('vector_db') else 'Loading'}")  
        st.write(f"✅ LLM: {'Ready' if models.get('llm') else 'Loading'}")
    else:
        st.error(f"⚠️ System Error: {stats['error']}")
    
    st.divider()
    
    # Quick actions
    st.header("⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Sync CVs", help="Download latest CV files from Google Drive"):
            with st.spinner("Syncing..."):
                import subprocess
                result = subprocess.run(["python", "sync_data.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("✅ Sync complete")
                else:
                    st.error("❌ Sync failed")
    
    with col2:
        if st.button("🔧 Rebuild DB", help="Rebuild vector database from CV files"):
            with st.spinner("Rebuilding..."):
                import subprocess
                result = subprocess.run(["python", "data_science_eda.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("✅ Rebuild complete")
                    # Clear model cache to reload
                    st.session_state.models_warmed = False
                    st.rerun()
                else:
                    st.error("❌ Rebuild failed")
    
    # EDA Report
    st.divider()
    st.header("📈 EDA Report")
    eda_path = Path("./assets/eda_report.png")
    if eda_path.exists():
        st.image(str(eda_path), caption="CV Chunk Analysis", use_container_width=True)
    else:
        st.info("Run data_science_eda.py to generate report")

# ---------------------------------------------------------------------------
# Main Chat Interface
# ---------------------------------------------------------------------------

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show performance metrics for assistant messages
        if message["role"] == "assistant" and "timing" in message:
            timing = message["timing"]
            if not timing.get("error"):
                cols = st.columns(4)
                cols[0].metric("⚡ Total", f"{timing['total']:.2f}s")
                cols[1].metric("🔍 Search", f"{timing['search']:.2f}s") 
                cols[2].metric("🤖 LLM", f"{timing['llm']:.2f}s")
                cols[3].metric("📚 Sources", len(message.get("sources", [])))

# Chat input
if prompt := st.chat_input("Ask about the CVs (e.g., 'What skills do candidates have?')"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing CVs..."):
            start_time = time.time()
            
            # Use optimized query function
            result = query_pagie_fast(prompt, k=6)
            
            response = result["answer"]
            sources = result.get("sources", [])
            timing = result.get("timing", {})
            
            st.markdown(response)
            
            # Show sources
            if sources:
                st.write("**Sources:**")
                source_cols = st.columns(len(sources))
                for i, source in enumerate(sources):
                    with source_cols[i]:
                        st.badge(source, type="secondary")
            
            # Show timing info
            if not timing.get("error"):
                cols = st.columns(4)
                cols[0].metric("⚡ Total", f"{timing['total']:.2f}s")
                cols[1].metric("🔍 Search", f"{timing['search']:.2f}s")
                cols[2].metric("🤖 LLM", f"{timing['llm']:.2f}s") 
                cols[3].metric("📚 Sources", len(sources))
    
    # Add assistant message with metadata
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "sources": sources,
        "timing": timing
    })
    
    # Update query count
    st.session_state.query_count += 1

# ---------------------------------------------------------------------------
# Footer - Performance Tips
# ---------------------------------------------------------------------------
with st.expander("⚡ Performance Tips"):
    st.markdown("""
    **Why is PAGie now faster?**
    
    1. **Model Pre-loading**: AI models are loaded once at startup (8s → instant)
    2. **Embedding Caching**: Query embeddings are cached (2.6s → ~0.1s for repeated queries)  
    3. **Optimized Context**: Smaller context windows for faster LLM processing
    4. **Singleton Pattern**: Models stay loaded in memory between queries
    5. **Streamlined Pipeline**: Reduced overhead in data processing
    
    **First query**: ~3-5 seconds (normal)  
    **Subsequent queries**: ~1-2 seconds (cached)
    
    **Tips for best performance:**
    - Use similar queries to benefit from embedding cache
    - Keep the app running to maintain loaded models
    - Use development mode (local Ollama) for fastest responses
    """)

# Display current mode in footer
mode = "Production (Gemini)" if st.session_state.get("app_mode") == "prod" else "Development (Ollama)"
st.markdown(f"*Running in {mode} mode*")