"""
rag_pipeline_local.py — Local-Only RAG Pipeline for PAGie
==========================================================
Pure local version of the RAG pipeline with NO cloud detection.
This version is optimized for local development with local paths only.

Key Features:
  - Local ChromaDB (./chroma_db)
  - Local embedding cache (./cache)
  - Google Gemini 3.0 or Ollama
  - No Streamlit Cloud detection
  - No GCS sync logic

Architecture: User Query → Query Enhancement → Fast Cached Retrieval → Smart Context → Gemini → Answer
"""

import hashlib
import logging
import os
import pickle
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple

import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser

try:
    from langchain_ollama import ChatOllama
except Exception:
    ChatOllama = None

# Performance optimizations
import warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ---------------------------------------------------------------------------
# Set up logging (MUST be before any logger usage)
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configuration from environment (with sensible defaults)
APP_MODE = os.getenv("APP_MODE", "dev").lower()  # dev|prod
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
LOCAL_LLM_PROVIDER = os.getenv("LOCAL_LLM_PROVIDER", "ollama").lower()
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen3.5:0.8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ALLOW_429_FALLBACK_TO_LOCAL = os.getenv("ALLOW_429_FALLBACK_TO_LOCAL", "true").lower() == "true"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# LOCAL PATHS ONLY - No cloud detection
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_CACHE_PATH = "./cache/embeddings_v2.pkl"
ENVIRONMENT = "local"

logger.info(f"🏠 Environment: {ENVIRONMENT} | ChromaDB path: {CHROMA_DB_PATH}")

RETRIEVAL_MULTIPLIER = int(os.getenv("RETRIEVAL_MULTIPLIER", "3"))  # Fetch k * multiplier candidates
MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", "30"))             # Upper limit for candidates
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "5000"))     # Balanced context size

# Performance settings - Enhanced caching
ENABLE_EMBEDDING_CACHE = True
CACHE_AUTO_SAVE_INTERVAL = 5  # Save every 5 new embeddings
CACHE_VERSION = "v2.0"  # For cache invalidation

# ---------------------------------------------------------------------------
# Global model instances for performance (Singleton Pattern)
# ---------------------------------------------------------------------------
_embedding_model_instance = None
_vector_db_instance = None
_llm_model_instance = None
_embedding_cache = {}
_cache_hits = 0
_cache_misses = 0

def _get_embedding_model():
    """Get or create singleton embedding model instance."""
    global _embedding_model_instance
    if _embedding_model_instance is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        start_time = time.time()
        _embedding_model_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            show_progress=False,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        load_time = time.time() - start_time
        logger.info(f"Embedding model loaded in {load_time:.2f}s")
    return _embedding_model_instance

def _get_vector_db():
    """Get or create singleton vector database instance."""
    global _vector_db_instance
    if _vector_db_instance is None:
        logger.info(f"Connecting to ChromaDB at {CHROMA_DB_PATH}")
        
        # Debug: Check if ChromaDB path exists
        chroma_path = Path(CHROMA_DB_PATH)
        logger.info(f"🔍 DEBUG: ChromaDB path exists? {chroma_path.exists()}")
        if chroma_path.exists():
            files = list(chroma_path.iterdir())
            logger.info(f"🔍 DEBUG: Files in ChromaDB: {[f.name for f in files]}")
            sqlite_file = chroma_path / "chroma.sqlite3"
            if sqlite_file.exists():
                size = sqlite_file.stat().st_size
                logger.info(f"🔍 DEBUG: chroma.sqlite3 size: {size} bytes")
            else:
                logger.error(f"🔍 DEBUG: chroma.sqlite3 MISSING!")
        else:
            logger.error(f"🔍 DEBUG: ChromaDB path {CHROMA_DB_PATH} does NOT exist!")
        
        embedding_model = _get_embedding_model()
        
        try:
            # Try to connect to existing ChromaDB (use default "langchain" collection name)
            _vector_db_instance = Chroma(
                persist_directory=CHROMA_DB_PATH,
                embedding_function=embedding_model
            )
            chunk_count = _vector_db_instance._collection.count()
            logger.info(f"Connected to ChromaDB with {chunk_count} chunks")
        except Exception as e:
            logger.warning(f"Failed to connect to existing ChromaDB: {e}")
            logger.info("Creating new ChromaDB collection...")
            
            # Create new collection if it doesn't exist or has issues
            _vector_db_instance = Chroma(
                persist_directory=CHROMA_DB_PATH,
                embedding_function=embedding_model
            )
            chunk_count = _vector_db_instance._collection.count()
            logger.info(f"Created new ChromaDB collection with {chunk_count} chunks")
    
    return _vector_db_instance

def _get_llm_model(provider: str = None):
    """Get or create singleton LLM model instance."""
    global _llm_model_instance
    if provider is None:
        provider = "gemini" if APP_MODE == "prod" else LOCAL_LLM_PROVIDER
    
    if _llm_model_instance is None:
        _llm_model_instance = _build_chat_model(provider)
    return _llm_model_instance

def _build_chat_model(provider: str):
    """Build chat model with enhanced configuration."""
    provider = provider.lower()

    if provider == "gemini":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when provider=gemini")
        logger.info(f"Using Gemini model: {GEMINI_MODEL}")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.6,
            max_tokens=1500,
        )

    if provider == "ollama":
        if ChatOllama is None:
            raise ImportError("langchain-ollama is not installed. Install it via requirements.txt")
        
        logger.info(f"Using local Ollama model: {LOCAL_LLM_MODEL} @ {OLLAMA_BASE_URL}")
        return ChatOllama(
            model=LOCAL_LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.6,
        )

    raise ValueError(f"Unsupported provider: {provider}")

# ---------------------------------------------------------------------------
# Enhanced Embedding Cache with SHA256 and TTL
# ---------------------------------------------------------------------------
def _get_cache_key(text: str) -> str:
    """Generate deterministic cache key using SHA256."""
    return hashlib.sha256(f"{CACHE_VERSION}:{text.strip()}".encode()).hexdigest()

def _load_embedding_cache():
    """Load embedding cache from disk."""
    global _embedding_cache
    if ENABLE_EMBEDDING_CACHE and Path(EMBEDDING_CACHE_PATH).exists():
        try:
            with open(EMBEDDING_CACHE_PATH, 'rb') as f:
                _embedding_cache = pickle.load(f)
            logger.info(f"Loaded {len(_embedding_cache)} cached embeddings")
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            _embedding_cache = {}

def _save_embedding_cache():
    """Save embedding cache to disk."""
    if not ENABLE_EMBEDDING_CACHE:
        return
    
    try:
        os.makedirs(Path(EMBEDDING_CACHE_PATH).parent, exist_ok=True)
        with open(EMBEDDING_CACHE_PATH, 'wb') as f:
            pickle.dump(_embedding_cache, f)
        logger.debug(f"Saved {len(_embedding_cache)} embeddings to cache")
    except Exception as e:
        logger.warning(f"Failed to save embedding cache: {e}")

def _get_cached_embedding(text: str) -> Optional[np.ndarray]:
    """Get cached embedding for text."""
    global _cache_hits, _cache_misses
    if not ENABLE_EMBEDDING_CACHE:
        return None
    
    cache_key = _get_cache_key(text)
    if cache_key in _embedding_cache:
        _cache_hits += 1
        logger.debug(f"Cache hit for query (hits: {_cache_hits}, misses: {_cache_misses})")
        return _embedding_cache[cache_key]
    
    _cache_misses += 1
    return None

def _cache_embedding(text: str, embedding: np.ndarray):
    """Cache embedding for text."""
    global _embedding_cache
    if not ENABLE_EMBEDDING_CACHE:
        return
    
    cache_key = _get_cache_key(text)
    _embedding_cache[cache_key] = embedding
    
    # Auto-save every N embeddings
    if len(_embedding_cache) % CACHE_AUTO_SAVE_INTERVAL == 0:
        _save_embedding_cache()

# ---------------------------------------------------------------------------
# Query Enhancement
# ---------------------------------------------------------------------------
def enhance_query(query: str) -> str:
    """
    Enhance user query with context-aware expansions.
    Example: "skills" → "skills experience qualifications expertise"
    """
    # Common CV/resume related query expansions
    expansions = {
        "skills": "skills experience qualifications expertise competencies",
        "education": "education degree university qualification academic",
        "work": "work experience employment job career position",
        "project": "project portfolio work achievement accomplishment",
        "contact": "contact email phone address linkedin",
    }
    
    query_lower = query.lower()
    for key, expansion in expansions.items():
        if key in query_lower:
            logger.debug(f"Expanding query '{query}' with: {expansion}")
            return f"{query} {expansion}"
    
    return query

# ---------------------------------------------------------------------------
# Fast Retrieval with Diversity
# ---------------------------------------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def retrieve_relevant_chunks(query: str, k: int = 5) -> List[Document]:
    """
    Retrieve relevant chunks with intelligent diversity.
    
    Strategy:
    1. Fetch k * RETRIEVAL_MULTIPLIER candidates (up to MAX_CANDIDATES)
    2. Diversify by source to avoid bias
    3. Return top k most relevant chunks
    """
    try:
        db = _get_vector_db()
        
        # Enhanced query
        enhanced_q = enhance_query(query)
        
        # Check embedding cache first
        cached_emb = _get_cached_embedding(enhanced_q)
        
        if cached_emb is not None:
            # Use cached embedding for similarity search
            n_candidates = min(k * RETRIEVAL_MULTIPLIER, MAX_CANDIDATES)
            results = db.similarity_search_by_vector(
                embedding=cached_emb.tolist(),
                k=n_candidates
            )
        else:
            # Generate new embedding and cache it
            embedding_model = _get_embedding_model()
            query_embedding = embedding_model.embed_query(enhanced_q)
            _cache_embedding(enhanced_q, np.array(query_embedding))
            
            n_candidates = min(k * RETRIEVAL_MULTIPLIER, MAX_CANDIDATES)
            results = db.similarity_search_by_vector(
                embedding=query_embedding,
                k=n_candidates
            )
        
        # Diversify by source
        diverse_chunks = _diversify_by_source(results, k)
        
        logger.info(f"Retrieved {len(diverse_chunks)} chunks (from {len(results)} candidates)")
        return diverse_chunks
        
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return []

def _diversify_by_source(docs: List[Document], k: int) -> List[Document]:
    """
    Select diverse chunks from different sources to avoid bias.
    """
    if len(docs) <= k:
        return docs
    
    # Group by source
    by_source = defaultdict(list)
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        by_source[source].append(doc)
    
    # Round-robin selection from different sources
    selected = []
    source_keys = list(by_source.keys())
    idx = 0
    
    while len(selected) < k and any(by_source.values()):
        source = source_keys[idx % len(source_keys)]
        if by_source[source]:
            selected.append(by_source[source].pop(0))
        idx += 1
    
    return selected[:k]

# ---------------------------------------------------------------------------
# Smart Context Building
# ---------------------------------------------------------------------------
def build_context(chunks: List[Document], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    Build context from retrieved chunks with intelligent truncation.
    """
    if not chunks:
        return "No relevant information found in the knowledge base."
    
    context_parts = []
    current_length = 0
    
    for i, doc in enumerate(chunks, 1):
        source = doc.metadata.get("source", "unknown")
        content = doc.page_content.strip()
        
        # Format: [1] filename: content
        chunk_text = f"[{i}] {Path(source).stem}: {content}"
        chunk_len = len(chunk_text)
        
        if current_length + chunk_len > max_chars:
            # Truncate last chunk to fit
            remaining = max_chars - current_length
            if remaining > 100:  # Only include if meaningful
                chunk_text = chunk_text[:remaining] + "..."
                context_parts.append(chunk_text)
            break
        
        context_parts.append(chunk_text)
        current_length += chunk_len
    
    return "\n\n".join(context_parts)

# ---------------------------------------------------------------------------
# Enhanced Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are PAGie, an intelligent CV/Resume analysis assistant.
Your knowledge base contains CV/Resume documents from various candidates.

Guidelines:
- Provide accurate, specific answers based on the provided context
- If information is not in the context, clearly state that
- Be concise but complete
- When comparing candidates, be objective and fair
- Always cite the source (candidate name) when referencing specific information
"""

def create_rag_prompt(query: str, context: str) -> str:
    """Create enhanced RAG prompt."""
    return f"""{SYSTEM_PROMPT}

Context from CV Knowledge Base:
{context}

User Question: {query}

Answer (be specific and cite sources):"""

# ---------------------------------------------------------------------------
# Core RAG Chain
# ---------------------------------------------------------------------------
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def query_pagie(query: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Main RAG query function with intelligent retrieval and response.
    
    Args:
        query: User question
        chat_history: Optional chat history for context
    
    Returns:
        Dict with answer, sources, and metadata
    """
    start_time = time.time()
    
    try:
        # Step 1: Retrieve relevant chunks
        chunks = retrieve_relevant_chunks(query, k=5)
        
        if not chunks:
            return {
                "answer": "I don't have enough information in my knowledge base to answer that question. Please try syncing your CV files first.",
                "sources": [],
                "chunks_used": 0,
                "retrieval_time": time.time() - start_time
            }
        
        # Step 2: Build context
        context = build_context(chunks)
        
        # Step 3: Create prompt
        prompt = create_rag_prompt(query, context)
        
        # Step 4: Get LLM response
        llm = _get_llm_model()
        response = llm.invoke(prompt)
        
        # Extract answer
        if hasattr(response, 'content'):
            answer = response.content
        else:
            answer = str(response)
        
        # Collect sources
        sources = list(set([
            Path(doc.metadata.get("source", "unknown")).stem 
            for doc in chunks
        ]))
        
        total_time = time.time() - start_time
        
        return {
            "answer": answer.strip(),
            "sources": sources,
            "chunks_used": len(chunks),
            "retrieval_time": total_time,
            "llm_model": GEMINI_MODEL if APP_MODE == "prod" else LOCAL_LLM_MODEL
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        
        # Fallback to local LLM if Gemini 429 error
        if "429" in str(e) and ALLOW_429_FALLBACK_TO_LOCAL and ChatOllama:
            logger.warning("Gemini rate limit hit, falling back to local Ollama...")
            try:
                # Retry with local LLM
                global _llm_model_instance
                _llm_model_instance = _build_chat_model("ollama")
                return query_pagie(query, chat_history)
            except Exception as fallback_error:
                logger.error(f"Fallback to Ollama failed: {fallback_error}")
        
        return {
            "answer": f"An error occurred: {str(e)}",
            "sources": [],
            "chunks_used": 0,
            "retrieval_time": time.time() - start_time
        }

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------
def warmup_models():
    """Pre-load models for faster first query."""
    logger.info("Warming up models...")
    _load_embedding_cache()
    _get_embedding_model()
    _get_vector_db()
    _get_llm_model()
    logger.info("Models ready!")

def get_db_stats() -> Dict[str, Any]:
    """Get database statistics."""
    try:
        db = _get_vector_db()
        chunk_count = db._collection.count()
        
        return {
            "status": f"Connected ({chunk_count} chunks)",
            "total_chunks": chunk_count,
            "app_mode": APP_MODE,
            "llm_model": GEMINI_MODEL if APP_MODE == "prod" else LOCAL_LLM_MODEL,
            "environment": ENVIRONMENT
        }
    except Exception as e:
        return {
            "status": f"Error: {str(e)}",
            "total_chunks": 0,
            "app_mode": APP_MODE,
            "llm_model": "unknown",
            "environment": ENVIRONMENT
        }

def get_cache_stats() -> Dict[str, Any]:
    """Get embedding cache statistics."""
    total = _cache_hits + _cache_misses
    hit_rate = _cache_hits / total if total > 0 else 0
    
    return {
        "cache_size": len(_embedding_cache),
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
        "hit_rate": hit_rate
    }

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
# Load cache on module import
_load_embedding_cache()

# Save cache on exit
import atexit
atexit.register(_save_embedding_cache)
