"""
rag_pipeline.py — Core RAG Logic for PAGie
============================================
This module is the "Brain" of PAGie. It handles:
  1. Connecting to the ChromaDB vector database.
  2. Performing semantic similarity search to retrieve relevant context.
  3. Augmenting the user's query with that context.
  4. Generating a grounded, accurate answer via Google Gemini.

Architecture: User Query → ChromaDB Retrieval → Prompt Augmentation → Gemini → Answer
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import HumanMessage, SystemMessage

# Load all API keys from the .env file — NEVER hardcode credentials.
load_dotenv()

# ---------------------------------------------------------------------------
# 1. THE BRAIN — Google Gemini (LLM for Answer Generation)
# ---------------------------------------------------------------------------
# Using gemini-2.0-flash for its speed and large context window.
# The model name can be updated via the GEMINI_MODEL environment variable
# to use the latest available version (e.g., gemini-3.0-flash).
# ---------------------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,  # Low temperature for factual, grounded answers — reduces hallucination
)

# ---------------------------------------------------------------------------
# 2. THE MEMORY — Google Text Embeddings (converts text → vectors)
# ---------------------------------------------------------------------------
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# ---------------------------------------------------------------------------
# 3. PAGie's PERSONA — System Prompt Engineering
# ---------------------------------------------------------------------------
# This prompt gives PAGie strict rules to prevent hallucination and to ensure
# it only answers based on the student's personal knowledge base.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are PAGie, a highly accurate AI Second Brain assistant for a CADT university student.
Your knowledge comes EXCLUSIVELY from the documents and notes stored in your vector database.

STRICT RULES:
1. ONLY answer using the provided context. Do NOT use any outside knowledge or make assumptions.
2. If the answer is not found in the context, respond with:
   "I couldn't find that in your knowledge base. Try syncing new documents first."
3. When referencing information, cite the source document name when available.
4. Be concise, structured, and academically appropriate in tone.
5. Never fabricate deadlines, names, dates, or any factual data."""


def get_vector_db() -> Chroma:
    """
    Establishes a connection to the persisted local ChromaDB instance.

    The database is built by data_science_eda.py and lives at ./chroma_db/.
    This function is called on every query to ensure a fresh connection.

    Returns:
        A Chroma vector store object ready for similarity search.

    Raises:
        ConnectionError: If the ChromaDB directory is missing or corrupt.
    """
    try:
        vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
        )
        return vector_db
    except Exception as e:
        raise ConnectionError(f"Failed to connect to ChromaDB at ./chroma_db: {e}")


def query_pagie(user_question: str, k: int = 4) -> dict:
    """
    The core RAG (Retrieval-Augmented Generation) function.

    This implements the full RAG pipeline in 3 steps:
      - RETRIEVE: Search ChromaDB for the top-k most semantically similar chunks.
      - AUGMENT:  Inject retrieved chunks as context into the Gemini prompt.
      - GENERATE: Call Gemini to produce a grounded, context-aware answer.

    Args:
        user_question (str): The natural language question from the user.
        k (int): Number of context chunks to retrieve (default: 4).

    Returns:
        dict: {
            "answer": (str) The generated answer from Gemini,
            "sources": (list) Unique source file paths that contributed context
        }
    """
    try:
        db = get_vector_db()

        # RETRIEVE: Find the top-k most relevant chunks via cosine similarity
        docs = db.similarity_search(user_question, k=k)

        if not docs:
            return {
                "answer": (
                    "⚠️ Your knowledge base appears to be empty. "
                    "Please run the sync and rebuild pipeline first."
                ),
                "sources": [],
            }

        # AUGMENT: Build a structured context string with source labels
        context_text = "\n\n---\n\n".join([
            f"[Source: {Path(doc.metadata.get('source', 'Unknown')).name}]\n{doc.page_content}"
            for doc in docs
        ])

        # GENERATE: Send the augmented prompt to Gemini
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Context retrieved from your personal knowledge base:\n\n"
                    f"{context_text}\n\n"
                    f"---\n"
                    f"Student's Question: {user_question}"
                )
            ),
        ]

        response = llm.invoke(messages)

        # Collect unique source file names for citation in the UI
        sources = list(set([
            doc.metadata.get("source", "Unknown") for doc in docs
        ]))

        return {"answer": response.content, "sources": sources}

    except ConnectionError as e:
        return {"answer": str(e), "sources": []}
    except Exception as e:
        return {"answer": f"An unexpected error occurred: {e}", "sources": []}


def get_db_stats() -> dict:
    """
    Returns basic health statistics about the ChromaDB collection.

    This is called by the Streamlit sidebar to display real-time system status,
    giving the user confidence that the knowledge base is active and populated.

    Returns:
        dict: {"total_chunks": int, "status": str}
    """
    try:
        db = get_vector_db()
        count = db._collection.count()
        return {"total_chunks": count, "status": "✅ Connected"}
    except Exception:
        return {"total_chunks": 0, "status": "❌ Not Connected"}


# ---------------------------------------------------------------------------
# Quick test — run this file directly to verify the pipeline works.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🧠 Testing PAGie RAG Pipeline...")
    result = query_pagie("When is my Data Science assignment due?")
    print(f"\nAnswer: {result['answer']}")
    print(f"Sources: {result['sources']}")