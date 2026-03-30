"""
app.py — Streamlit Frontend for PAGie
======================================
A professional, ChatGPT-style chat interface for PAGie.

Features:
  - Real-time conversational chat with session history.
  - Source citation badges displayed beneath each AI response.
  - Sidebar showing live system health, DB stats, and the EDA report.
  - One-click "Sync" and "Rebuild Knowledge Base" actions.
  - PAGie persona with a clean, academic-friendly UI.

Usage:
  streamlit run app.py
"""

from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag_pipeline import get_db_stats, query_pagie

load_dotenv()


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
    page_title="PAGie — Second Brain",
    page_icon="🧠",
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

        /* Source citation badge */
        .source-badge {
            background-color: #eef2ff;
            border: 1px solid #c7d2fe;
            border-radius: 6px;
            padding: 3px 9px;
            font-size: 0.72rem;
            color: #4338ca;
            display: inline-block;
            margin: 3px 2px;
            font-family: monospace;
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
    </style>
    """,
    unsafe_allow_html=True,
)


# ===========================================================================
# SIDEBAR — System Status & Controls
# ===========================================================================

with st.sidebar:
    st.markdown("## 🧠 PAGie")
    st.caption("Personal AI Generation & Information Engine")
    st.markdown("**CADT · Group 5 · Data Science Project**")
    st.divider()

    # --- Live Database Health ---
    st.markdown("### 📡 System Status")
    stats = get_db_stats()
    status_color = "🟢" if "Connected" in stats["status"] else "🔴"
    st.markdown(f"{status_color} **Vector DB:** {stats['status']}")
    st.caption(f"Mode: {stats.get('app_mode', 'unknown')} · LLM: {stats.get('llm_provider', 'n/a')} ({stats.get('llm_model', 'n/a')})")

    col1, col2 = st.columns(2)
    col1.metric("📦 Chunks", stats["total_chunks"])

    # Read and display the last sync timestamp.
    last_sync_path = Path("./data/last_sync.txt")
    if last_sync_path.exists():
        with open(last_sync_path, "r") as f:
            raw_ts = f.read().strip()
        try:
            dt = datetime.fromisoformat(raw_ts)
            col2.metric("🕐 Last Sync", dt.strftime("%b %d, %H:%M"))
        except ValueError:
            col2.metric("🕐 Last Sync", raw_ts[:16])
    else:
        col2.metric("🕐 Last Sync", "Never")

    st.divider()

    # --- Action Buttons ---
    st.markdown("### ⚙️ Actions")

    if st.button("🔄 Sync Data Sources", width="stretch", help="Fetch latest files from Google Drive & Notion"):
        with st.spinner("Connecting to Google Drive & Notion..."):
            try:
                from sync_data import run_sync
                run_sync()
                st.success("✅ Sync complete!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Sync failed: {e}")

    if st.button("🔬 Rebuild Knowledge Base", width="stretch", help="Re-process documents: chunk → IQR filter → embed → store"):
        with st.spinner("Running Data Science pipeline (this may take a minute)..."):
            try:
                from data_science_eda import run_pipeline
                df, _ = run_pipeline()
                if df is not None:
                    st.success(f"✅ Done! {len(df)} clean chunks indexed.")
                    st.rerun()
                else:
                    st.warning("⚠️ No documents found. Sync first.")
            except Exception as e:
                st.error(f"❌ Pipeline failed: {e}")

    if st.button("🗑️ Clear Chat History", width="stretch"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # --- EDA Report Viewer ---
    st.markdown("### 📊 EDA Report")
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
    st.caption("Built with LangChain · ChromaDB · Gemini · Streamlit")


# ===========================================================================
# MAIN CHAT INTERFACE
# ===========================================================================

st.title("🧠 PAGie — Your Personal AI Second Brain")
st.caption(
    "Ask me anything from your **Google Drive** & **Notion** knowledge base. "
    "I only answer from your personal documents — no hallucinations."
)

# ---------------------------------------------------------------------------
# Session State — preserves chat history across Streamlit reruns.
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I’m **PAGie**, speaking as your knowledge-backed version of you.\n\n"
                "When I answer, I’ll respond in **first person** using your synced notes, "
                "documents, and project materials. Ask me things like interview questions, "
                "project updates, academic background, or anything stored in your knowledge base.\n\n"
                "*What would you like me to answer as you today?*"
            ),
            "sources": [],
        }
    ]

# ---------------------------------------------------------------------------
# Render full chat history
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    avatar = "🧠" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

        # Render source citation badges below each assistant response.
        if message["role"] == "assistant" and message.get("sources"):
            badges_html = "".join([
                f'<span class="source-badge">📄 {Path(s).name}</span>'
                for s in message["sources"]
            ])
            st.markdown(
                f"<small><b>📎 Sources:</b></small><br>{badges_html}",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Chat Input — captures the user's next message
# ---------------------------------------------------------------------------
if prompt := st.chat_input(
    "Ask PAGie anything... e.g. 'When is my Data Science assignment due?'"
):
    # 1. Display & store the user's message immediately.
    st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Query PAGie and stream the response.
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Searching your knowledge base..."):
            result = query_pagie(prompt)

        answer_text = _to_display_text(result.get("answer", ""))

        st.markdown(answer_text)

        # Render source badges for the new response.
        if result.get("sources"):
            badges_html = "".join([
                f'<span class="source-badge">📄 {Path(s).name}</span>'
                for s in result["sources"]
            ])
            st.markdown(
                f"<small><b>📎 Sources:</b></small><br>{badges_html}",
                unsafe_allow_html=True,
            )

    # 3. Persist the assistant response to session history.
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "sources": result.get("sources", []),
    })
