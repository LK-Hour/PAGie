"""
app.py — Streamlit Frontend for PAGie (CV Analysis System)
===========================================================
A professional, ChatGPT-style chat interface for PAGie's CV analysis system.

Features:
  - Real-time conversational chat with session history.
  - Source citation badges showing which CV files were referenced.
  - Sidebar showing live system health, DB stats, and the EDA report.
  - One-click "Sync" and "Rebuild Knowledge Base" actions.
  - PAGie persona optimized for answering questions about candidate CVs.

Usage:
  streamlit run app.py
"""

from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag_pipeline import query_pagie, get_cache_stats, warmup_models
from chat_history import ChatHistoryManager, InputHistoryManager
try:
    # Try to get DB stats if available
    from rag_pipeline import get_db_stats
except (ImportError, AttributeError):
    def get_db_stats():
        return {"status": "Connected", "total_chunks": "N/A", "app_mode": "prod"}

load_dotenv()

# Initialize unified RAG pipeline
@st.cache_resource
def initialize_pagie():
    """Initialize and warm up PAGie models (cached for performance)."""
    try:
        warmup_models()
        return True
    except Exception as e:
        st.error(f"Failed to initialize PAGie: {e}")
        return False

# Warm up models on app start
initialize_pagie()

# Initialize chat history manager
chat_history_manager = ChatHistoryManager()
input_history_manager = InputHistoryManager()


def _to_display_text(value) -> str:
    """Converts mixed model payloads into clean text for Streamlit markdown."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            elif hasattr(item, "text") and getattr(item, "text"):
                parts.append(str(getattr(item, "text")))
        if parts:
            return "\n\n".join(parts)
    return str(value)

# ---------------------------------------------------------------------------
# Page Configuration — must be the FIRST Streamlit call in the script.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PAGie — CV Analysis System",
    page_icon="./assets/icon/PAGie_profile_64px.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Polishes the UI beyond Streamlit's default styles.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Chat message bubbles */
        .stChatMessage {
            border-radius: 14px;
            margin-bottom: 6px;
        }

        /* Sidebar section dividers */
        .sidebar-section {
            background-color: #f8fafc;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 10px;
        }

        /* Main title styling */
        h1 { padding-bottom: 0 !important; }
        
        /* Chat input - no borders at all */
        .stChatInput > div,
        .stChatInput > div > div,
        .stChatInput textarea,
        .stChatInput input,
        .stChatInputContainer,
        .stChatInputContainer > div,
        .stChatInputContainer textarea,
        .stChatInputContainer input {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        
        .stChatInput textarea:focus,
        .stChatInput input:focus,
        .stChatInputContainer textarea:focus,
        .stChatInputContainer input:focus {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        
        /* Tabs styling - indigo theme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
            color: #64748b !important;
        }
        
        /* Tab hover state - indigo instead of red */
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #f0f9ff !important;
            color: #6366f1 !important;
        }
        
        /* Selected tab - indigo background */
        .stTabs [aria-selected="true"] {
            background-color: #6366f1 !important;
            color: white !important;
            border-bottom: 2px solid #6366f1 !important;
        }
        
        /* Remove any red underlines from tabs */
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #6366f1 !important;
        }
        
        /* Text input focus state - indigo instead of red */
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 1px #6366f1 !important;
        }
        
        /* Universal focus override - only outline, no extra borders */
        *:focus-visible {
            outline-color: #6366f1 !important;
            outline-width: 2px !important;
            outline-offset: 2px !important;
        }
        
        /* BaseWeb input overrides */
        [data-baseweb="input"]:focus-within,
        [data-baseweb="base-input"]:focus-within,
        [data-baseweb="textarea"]:focus-within {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 1px #6366f1 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===========================================================================
# SIDEBAR — System Status & Controls
# ===========================================================================

with st.sidebar:
    # Sidebar header with custom icon
    sidebar_col1, sidebar_col2 = st.columns([1, 4])
    
    with sidebar_col1:
        st.image("./assets/icon/PAGie_profile_64px.ico", width=40)
    
    with sidebar_col2:
        st.markdown("## PAGie")
    st.caption("Personal AI Generation & Information Engine")
    st.markdown("**CADT · Group 5 · Data Science Project**")
    
    # Show session ID for multi-user transparency
    from chat_history import get_session_id
    session_id = get_session_id()
    st.caption(f"Session: `{session_id}`")
    
    st.divider()

    # --- Live Database Health ---
    st.markdown("### :material/router: System Status")
    
    try:
        stats = get_db_stats()
        status_icon = ":material/check_circle:" if "Connected" in stats.get("status", "") else ":material/error:"
        st.markdown(f"{status_icon} **Vector DB:** {stats.get('status', 'Unknown')}")
        st.caption(f"Mode: {stats.get('app_mode', 'unknown')} · LLM: {stats.get('llm_provider', 'n/a')} ({stats.get('llm_model', 'n/a')})")
        
        col1, col2 = st.columns(2)
        col1.metric("Chunks", stats.get("total_chunks", "N/A"), help="Total text chunks in vector database")
        
        # Show cache performance
        cache_stats = get_cache_stats()
        hit_rate = cache_stats.get("hit_rate", 0) * 100
        col2.metric("Cache Hit", f"{hit_rate:.1f}%", help="Embedding cache performance")
        
    except Exception as e:
        st.markdown(":material/error: **Vector DB:** Error connecting")
        st.caption(f"Error: {str(e)[:50]}")
        col1, col2 = st.columns(2)
        col1.metric("Chunks", "N/A")
        col2.metric("Cache Hit", "N/A")

    # Read and display the last sync timestamp.
    last_sync_path = Path("./data/last_sync.txt")
    if last_sync_path.exists():
        with open(last_sync_path, "r") as f:
            raw_ts = f.read().strip()
        try:
            dt = datetime.fromisoformat(raw_ts)
            col2.metric("Last Sync", dt.strftime("%b %d, %H:%M"), help="Most recent data synchronization")
        except ValueError:
            col2.metric("Last Sync", raw_ts[:16])
    else:
        col2.metric("Last Sync", "Never")

    st.divider()

    # --- Action Buttons ---
    st.markdown("### :material/settings: Actions")

    if st.button(":material/sync: Sync CV Files", width="stretch", help="Fetch latest CV files from Google Drive folder"):
        with st.spinner("Connecting to Google Drive..."):
            try:
                from sync_data import run_sync
                run_sync()
                st.success("Sync complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Sync failed: {e}")

    if st.button(":material/science: Rebuild Knowledge Base", width="stretch", help="Re-process CV files: chunk → IQR filter → embed → store"):
        with st.spinner("Running Data Science pipeline (this may take a minute)..."):
            try:
                from data_science_eda import run_pipeline
                df, _ = run_pipeline()
                if df is not None:
                    st.success(f"Done! {len(df)} clean CV chunks indexed.")
                    st.rerun()
                else:
                    st.warning("No CV files found. Sync first.")
            except Exception as e:
                st.error(f"Pipeline failed: {e}")

    if st.button(":material/delete: Clear Chat History", width="stretch"):
        st.session_state.messages = []
        chat_history_manager.clear_history()
        input_history_manager.clear_inputs()
        st.rerun()

    st.divider()

    # --- EDA Report Viewer ---
    st.markdown("### :material/analytics: EDA Report")
    eda_path = Path("./assets/eda_report.png")
    if eda_path.exists():
        st.image(
            str(eda_path),
            width="stretch",
            caption="Latest IQR filtering & data distribution analysis",
        )
        # Show when the EDA was last generated
        import os
        mtime = os.path.getmtime(eda_path)
        st.caption(f"Generated: {datetime.fromtimestamp(mtime).strftime('%b %d %Y, %H:%M')}")
    else:
        st.info("No EDA report yet.\nClick 'Rebuild Knowledge Base' to generate one.")

    st.divider()

    # --- File Explorer Section ---
    st.markdown("### :material/folder: CV Files")
    
    cv_folder = Path("./data/drive")
    
    if cv_folder.exists():
        pdf_files = list(cv_folder.glob("*.pdf"))
        
        if pdf_files:
            # Sort by modification time
            pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            st.caption(f"Found {len(pdf_files)} CV files:")
            
            for pdf_file in pdf_files:
                stat = pdf_file.stat()
                file_size = stat.st_size
                
                # Format file size
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                with st.expander(f":material/description: {pdf_file.stem}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.caption(f"Size: {size_str}")
                        mod_time = datetime.fromtimestamp(stat.st_mtime)
                        st.caption(f"Modified: {mod_time.strftime('%b %d, %H:%M')}")
                    
                    with col2:
                        # Download button
                        with open(pdf_file, "rb") as file:
                            st.download_button(
                                label=":material/download: Download",
                                data=file.read(),
                                file_name=pdf_file.name,
                                mime="application/pdf",
                                key=f"download_original_{pdf_file.name}",
                                use_container_width=True
                            )
        else:
            st.info("No CV files found. Run 'Sync CV Files' first.")
    else:
        st.info("CV folder not found. Run 'Sync CV Files' first.")

    st.divider()
    st.caption("Built with LangChain · ChromaDB · Gemini · Streamlit")


# ===========================================================================
# MAIN CHAT INTERFACE
# ===========================================================================

# Create header with custom icon
header_col1, header_col2 = st.columns([1, 15])

with header_col1:
    st.image("./assets/icon/PAGie_profile_64px.ico", width=60)

with header_col2:
    st.title("PAGie — CV Analysis & Candidate Information System")
st.caption(
    "Ask me anything about the candidates in your **CV database**. "
    "I analyze resumes and provide accurate information based on the CV files."
)

# ---------------------------------------------------------------------------
# Session State — preserves chat history across Streamlit reruns.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Session State — Load chat history from disk or initialize with default
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    # Try to load existing history
    loaded_messages = chat_history_manager.load_history()
    
    if loaded_messages:
        # Use loaded history
        st.session_state.messages = loaded_messages
    else:
        # Initialize with welcome message
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I'm **PAGie**, speaking as your knowledge-backed version of you.\n\n"
                    "When I answer, I'll respond in **first person** using your synced notes, "
                    "documents, and project materials. Ask me things like interview questions, "
                    "project updates, academic background, or anything stored in your knowledge base.\n\n"
                    "*What would you like me to answer as you today?*"
                ),
                "sources": [],
            }
        ]

# Initialize input history index for navigation
if "input_history_index" not in st.session_state:
    st.session_state.input_history_index = -1


# ---------------------------------------------------------------------------
# Render full chat history
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    avatar = "./assets/icon/PAGie_profile_64px.ico" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

        # Source citations removed per user request
        # if message["role"] == "assistant" and message.get("sources"):
        #     unique_sources = list(dict.fromkeys(message["sources"]))
        #     badges_html = "".join([
        #         f'<span class="source-badge">{Path(s).name}</span>'
        #         for s in unique_sources
        #     ])
        #     st.markdown(
        #         f"<small><b>Sources:</b></small><br>{badges_html}",
        #         unsafe_allow_html=True,
        #     )

# ---------------------------------------------------------------------------
# Chat Input — captures the user's next message
# ---------------------------------------------------------------------------

# Add a recent prompts dropdown before the chat input
col_input, col_history = st.columns([4, 1])

with col_history:
    recent_inputs = input_history_manager.load_inputs()
    if recent_inputs:
        with st.popover(":material/history: Recent"):
            st.caption("Click to reuse a recent prompt:")
            for idx, past_input in enumerate(recent_inputs[:10]):  # Show last 10
                if st.button(
                    f"{past_input[:50]}..." if len(past_input) > 50 else past_input,
                    key=f"history_{idx}",
                    use_container_width=True
                ):
                    # Set this as the current prompt
                    st.session_state['selected_prompt'] = past_input
                    st.rerun()

with col_input:
    # Check if we have a selected prompt from history
    default_value = st.session_state.get('selected_prompt', '')
    if default_value:
        # Clear the selected prompt after using it
        del st.session_state['selected_prompt']
    
    prompt = st.chat_input(
        "Ask about candidates... e.g. 'Who has Python experience?'",
        key="main_chat_input"
    )
    
    # If we had a default value, use it as the prompt
    if not prompt and default_value:
        prompt = default_value

if prompt:
    # 1. Display & store the user's message immediately.
    st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
    
    # Save to input history for arrow key navigation
    input_history_manager.add_input(prompt)
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Query PAGie and stream the response.
    with st.chat_message("assistant", avatar="./assets/icon/PAGie_profile_64px.ico"):
        # Prepare chat history for context (exclude current user message and initial greeting)
        chat_history = []
        for msg in st.session_state.messages[1:-1]:  # Skip initial greeting and current message
            if msg["role"] in ["user", "assistant"]:
                chat_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        with st.spinner("Searching CV database..."):
            result = query_pagie(prompt, chat_history=chat_history)

        answer_text = _to_display_text(result.get("answer", ""))

        st.markdown(answer_text)

        # Source badges removed per user request
        # if result.get("sources"):
        #     unique_sources = list(dict.fromkeys(result["sources"]))
        #     badges_html = "".join([
        #         f'<span class="source-badge">{Path(s).name}</span>'
        #         for s in unique_sources
        #     ])
        #     st.markdown(
        #         f"<small><b>Sources:</b></small><br>{badges_html}",
        #         unsafe_allow_html=True,
        #     )

    # 3. Persist the assistant response to session history.
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "sources": result.get("sources", []),
    })
    
    # 4. Save chat history to disk for persistence across refreshes
    chat_history_manager.save_history(st.session_state.messages)
