"""
rag_pipeline_unified.py — High-Performance Unified RAG for PAGie
================================================================
Combines the best features from rag_pipeline.py and rag_pipeline_optimized.py:
  - Performance optimizations (caching, singletons, fast search) 
  - Intelligent retrieval (query rewriting, diversity selection)
  - Robust error handling (429 fallback, normalization)
  - Enhanced prompts for better accuracy

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
# Load environment variables and validate required keys
# ---------------------------------------------------------------------------
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configuration from environment (with sensible defaults)
APP_MODE = os.getenv("APP_MODE", "dev").lower()  # dev|prod
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
LOCAL_LLM_PROVIDER = os.getenv("LOCAL_LLM_PROVIDER", "ollama").lower()
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen3.5:0.8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ALLOW_429_FALLBACK_TO_LOCAL = os.getenv("ALLOW_429_FALLBACK_TO_LOCAL", "true").lower() == "true"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
RETRIEVAL_MULTIPLIER = int(os.getenv("RETRIEVAL_MULTIPLIER", "3"))  # Fetch k * multiplier candidates
MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", "30"))             # Upper limit for candidates
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "5000"))     # Balanced context size

# Performance settings - Enhanced caching
ENABLE_EMBEDDING_CACHE = True
EMBEDDING_CACHE_PATH = "./cache/embeddings_v2.pkl"
CACHE_AUTO_SAVE_INTERVAL = 5  # Save every 5 new embeddings
CACHE_VERSION = "v2.0"  # For cache invalidation

# ---------------------------------------------------------------------------
# Set up logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        embedding_model = _get_embedding_model()
        _vector_db_instance = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embedding_model
        )
        chunk_count = _vector_db_instance._collection.count()
        logger.info(f"Connected to ChromaDB with {chunk_count} chunks")
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
            temperature=0.15,  # Balanced for factuality + variety
            max_tokens=1024,   # Force conciseness
        )

    if provider == "ollama":
        if ChatOllama is None:
            raise ImportError("langchain-ollama is not installed. Install it via requirements.txt")
        logger.info(f"Using local Ollama model: {LOCAL_LLM_MODEL} @ {OLLAMA_BASE_URL}")
        return ChatOllama(
            model=LOCAL_LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.15,
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
    if not ENABLE_EMBEDDING_CACHE:
        return
    
    cache_key = _get_cache_key(text)
    _embedding_cache[cache_key] = embedding
    
    # Auto-save every N embeddings
    if len(_embedding_cache) % CACHE_AUTO_SAVE_INTERVAL == 0:
        _save_embedding_cache()

# ---------------------------------------------------------------------------
# Query Enhancement and Intent Detection
# ---------------------------------------------------------------------------
def _is_intro_query(query: str) -> bool:
    """Detect if query is asking for general introduction/overview."""
    intro_keywords = [
        "who is", "tell me about", "introduce", "introduction", "describe",
        "profile", "overview", "background", "summary", "about",
        "what can you tell me", "give me information"
    ]
    return any(keyword in query.lower() for keyword in intro_keywords)

def _rewrite_query_with_cv_keywords(original_query: str) -> str:
    """Enhance query with CV-specific keywords for better retrieval."""
    query_lower = original_query.lower()
    
    # CV-specific keyword expansion
    cv_keywords = []
    
    if any(word in query_lower for word in ["skill", "know", "proficient", "good at", "experience with"]):
        cv_keywords.extend(["skills", "technical proficiency", "programming", "tools", "languages", "frameworks"])
    
    if any(word in query_lower for word in ["work", "job", "position", "role", "experience"]):
        cv_keywords.extend(["experience", "work history", "position", "role", "employment", "career"])
    
    if any(word in query_lower for word in ["education", "study", "school", "university", "degree"]):
        cv_keywords.extend(["education", "academic", "degree", "university", "certification", "course"])
    
    if any(word in query_lower for word in ["project", "build", "develop", "create"]):
        cv_keywords.extend(["projects", "development", "implementation", "achievements", "portfolio"])
    
    # For intro queries, boost with profile keywords
    if _is_intro_query(original_query):
        cv_keywords.extend(["profile", "summary", "background", "overview", "personal", "professional"])
    
    # Combine original query with keywords
    if cv_keywords:
        enhanced_query = f"{original_query} {' '.join(set(cv_keywords))}"
        logger.debug(f"Enhanced query: '{original_query}' → '{enhanced_query}'")
        return enhanced_query
    
    return original_query

# ---------------------------------------------------------------------------
# Fast Retrieval with Smart Context Assembly
# ---------------------------------------------------------------------------
def _fast_similarity_search(db, query_embedding: np.ndarray, k: int) -> List[Document]:
    """Perform fast similarity search using vector directly."""
    try:
        # Try direct vector search (faster)
        search_start = time.time()
        docs = db.similarity_search_by_vector(query_embedding, k=k)
        search_time = time.time() - search_start
        logger.debug(f"Fast vector search completed in {search_time:.3f}s")
        return docs
    except Exception as e:
        # Fallback to standard search
        logger.debug(f"Vector search failed ({e}), using standard search")
        return db.similarity_search("", k=k)

def _diversity_selection(docs: List[Document], max_docs: int = 8) -> List[Document]:
    """Select diverse documents to avoid over-representation of single sources."""
    if len(docs) <= max_docs:
        return docs
    
    selected = []
    source_counts = defaultdict(int)
    
    # Greedy selection prioritizing diversity
    for doc in docs:
        source = doc.metadata.get('source', 'unknown')
        source_file = Path(source).stem if source != 'unknown' else 'unknown'
        
        # Calculate selection score (lower = higher priority)
        relevance_score = len(selected)  # Later docs have lower relevance
        diversity_penalty = source_counts[source_file] * 2  # Penalize over-representation
        selection_score = relevance_score + diversity_penalty
        
        # Select if we need more docs or this has a good score
        if len(selected) < max_docs:
            selected.append((selection_score, doc))
            source_counts[source_file] += 1
        else:
            # Replace worst doc if this is better
            selected.sort(key=lambda x: x[0])
            if selection_score < selected[-1][0]:
                selected[-1] = (selection_score, doc)
    
    # Return sorted by relevance (original order)
    return [doc for score, doc in selected]

def _assemble_context(docs: List[Document]) -> str:
    """Assemble context from documents with size limit."""
    context_parts = []
    current_length = 0
    
    for i, doc in enumerate(docs):
        content = doc.page_content.strip()
        if not content:
            continue
        
        # Calculate space needed
        source = doc.metadata.get('source', 'unknown')
        source_label = f"\n[Source: {Path(source).name}]"
        entry = f"{content}{source_label}\n"
        
        # Check if adding this would exceed limit
        if current_length + len(entry) > MAX_CONTEXT_CHARS:
            # Try to add partial content if enough space remains
            remaining_space = MAX_CONTEXT_CHARS - current_length
            if remaining_space > 200:  # Minimum useful space
                partial_content = content[:remaining_space-len(source_label)-10] + "..."
                context_parts.append(f"{partial_content}{source_label}")
            break
        
        context_parts.append(entry)
        current_length += len(entry)
    
    return "\n".join(context_parts)

# ---------------------------------------------------------------------------
# Enhanced Prompt Engineering
# ---------------------------------------------------------------------------
def _build_enhanced_prompt() -> str:
    """Build structured system prompt for accurate CV analysis."""
    return """You are PAGie, an expert CV analysis assistant with access to a database of professional profiles and resumes.

CORE PRINCIPLES:
• Answer ONLY based on the provided CV data - never fabricate information
• If information is unavailable, explicitly state "This information is not available in the provided CV data"
• Use third-person references (e.g., "John has experience with..." not "you have experience")
• Be concise but comprehensive - provide specific details when available

RESPONSE FORMAT:
🧠 **Summary:** [2-3 sentence overview directly answering the question]

**Details:**
• **Contact Information:** Phone, email, location (when available)
• **Technical Skills:** Programming languages, frameworks, databases, tools
• **Soft Skills:** Communication, leadership, teamwork abilities  
• **Languages:** Spoken language proficiencies
• **Education:** Academic background and institutions
• **Experience/Projects:** Work history and notable projects

CRITICAL FORMATTING RULES:
• DO NOT include any source citations within the text content
• DO NOT write "(Source: filename.pdf)" anywhere in your response
• DO NOT mention filenames in the main response text
• Present information cleanly without inline references
• Group related information together logically
• Use bullet points for lists and clear section headers

QUALITY STANDARDS:
• Prioritize recent and relevant information
• Include specific skills, experience years, technologies, and achievements when mentioned
• For comparison questions, present facts side-by-side without personal opinions
• If multiple candidates match criteria, mention all relevant ones
• Distinguish between skills (technical abilities) and experience (work history)

FORMATTING EXAMPLES:
✅ GOOD: **Programming Languages:** Python, JavaScript, PHP, C++
❌ BAD: **Programming Languages:** Python (Source: CV.pdf), JavaScript (Source: CV.pdf)

Remember: Clean, professional presentation without any source citations in the main content."""

# ---------------------------------------------------------------------------
# Core RAG Function with Enhanced Accuracy
# ---------------------------------------------------------------------------
def _is_resource_exhausted_error(err: Exception) -> bool:
    """Check if error indicates API quota exhaustion."""
    msg = str(err).lower()
    return "resource_exhausted" in msg or "429" in msg or "quota" in msg


def _extract_relevant_sources(selected_docs, answer_text: str, query: str) -> list:
    """
    Extract sources that are actually relevant to the response.
    
    Uses content overlap analysis to determine which sources contributed
    meaningful information to the answer.
    
    Args:
        selected_docs: Retrieved documents
        answer_text: Generated response text
        query: Original user query
        
    Returns:
        List of relevant source filenames
    """
    if not selected_docs or not answer_text:
        return []
    
    # Clean answer text for analysis (remove formatting)
    clean_answer = re.sub(r'[*#_`]', '', answer_text.lower())
    query_lower = query.lower()
    
    relevant_sources = []
    source_scores = {}
    
    for doc in selected_docs:
        source = doc.metadata.get('source', 'unknown')
        source_name = Path(source).name if source != 'unknown' else 'unknown'
        
        if source_name in source_scores:
            continue  # Already scored this source
            
        # Calculate relevance score based on content overlap
        doc_content = (doc.page_content or "").lower()
        
        # Score factors:
        score = 0
        
        # 1. Key terms from document appear in answer
        doc_words = set(re.findall(r'\b\w{3,}\b', doc_content))
        answer_words = set(re.findall(r'\b\w{3,}\b', clean_answer))
        overlap_ratio = len(doc_words.intersection(answer_words)) / max(len(answer_words), 1)
        score += overlap_ratio * 100
        
        # 2. Document relevance to query
        query_words = set(re.findall(r'\b\w{3,}\b', query_lower))
        query_relevance = len(doc_words.intersection(query_words)) / max(len(query_words), 1)
        score += query_relevance * 50
        
        # 3. Content length bonus (longer docs are more likely to be relevant)
        if len(doc_content) > 100:
            score += 10
            
        source_scores[source_name] = score
    
    # Select sources above relevance threshold, sorted by score
    threshold = 15  # Minimum relevance score
    relevant_sources = [
        source for source, score in sorted(
            source_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        ) 
        if score >= threshold
    ]
    
    # Ensure we have at least one source if documents were retrieved
    if not relevant_sources and selected_docs:
        # Fallback: include the highest-scoring source
        best_source = max(source_scores.items(), key=lambda x: x[1])[0]
        relevant_sources = [best_source]
    
    return relevant_sources


def _normalize_llm_text(content: Any) -> str:
    """Normalize various LLM response formats to clean text."""
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list) and len(content) > 0:
        if hasattr(content[0], 'text'):
            return content[0].text.strip()
        elif isinstance(content[0], dict) and 'text' in content[0]:
            return content[0]['text'].strip()
        else:
            return str(content[0]).strip()
    elif hasattr(content, 'text'):
        return content.text.strip()
    else:
        return str(content).strip()

def query_pagie(user_question: str, k: int = 8) -> Dict[str, Any]:
    """
    Enhanced RAG function combining performance optimizations with intelligent retrieval.
    
    Args:
        user_question (str): The natural language question.
        k (int): Number of context chunks to retrieve.
    
    Returns:
        dict: {"answer": str, "sources": list}
    """
    try:
        start_time = time.time()
        logger.info(f"Processing query: {user_question}")
        
        # Step 1: Query enhancement with CV-specific keywords
        enhanced_query = _rewrite_query_with_cv_keywords(user_question)
        logger.info(f"Enhanced query: {enhanced_query}")
        
        # Step 2: Fast embedding with caching
        cached_embedding = _get_cached_embedding(enhanced_query)
        if cached_embedding is not None:
            query_embedding = cached_embedding
        else:
            embed_start = time.time()
            embedding_model = _get_embedding_model()
            query_embedding = np.array(embedding_model.embed_query(enhanced_query))
            _cache_embedding(enhanced_query, query_embedding)
            embed_time = time.time() - embed_start
            logger.debug(f"Query embedded in {embed_time:.3f}s")
        
        # Step 3: Intelligent retrieval with diversity selection
        vector_db = _get_vector_db()
        
        # Calculate retrieval parameters
        fetch_count = min(k * RETRIEVAL_MULTIPLIER, MAX_CANDIDATES)
        
        # Fast similarity search
        raw_docs = _fast_similarity_search(vector_db, query_embedding, fetch_count)
        
        # Apply diversity selection
        selected_docs = _diversity_selection(raw_docs, k)
        
        logger.debug(f"Retrieved {len(selected_docs)} docs from {len(raw_docs)} candidates")
        
        # Step 4: Assemble context with size optimization
        context_text = _assemble_context(selected_docs)
        context_length = len(context_text)
        logger.debug(f"Context assembled: {context_length} chars")
        
        # Step 5: Enhanced prompt construction
        system_prompt = _build_enhanced_prompt()
        task_prompt = f"""
<context>
{context_text}
</context>

<task>
Question: {user_question}
Analyze the CV data above and provide a structured answer following the specified format.
</task>
"""
        
        # Step 6: LLM inference with fallback handling
        llm_start = time.time()
        primary_provider = "gemini" if APP_MODE == "prod" else LOCAL_LLM_PROVIDER
        
        try:
            llm_model = _get_llm_model(primary_provider)
            chain = llm_model | StrOutputParser()
            response = chain.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_prompt}
            ])
        except Exception as model_err:
            # Enhanced fallback handling
            if (
                primary_provider == "gemini"
                and ALLOW_429_FALLBACK_TO_LOCAL
                and _is_resource_exhausted_error(model_err)
            ):
                logger.warning("Gemini quota exhausted. Falling back to local model.")
                try:
                    fallback_model = _build_chat_model("ollama")
                    response = (fallback_model | StrOutputParser()).invoke([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": task_prompt}
                    ])
                except Exception as fallback_err:
                    logger.error(f"Fallback model also failed: {fallback_err}")
                    return {
                        "answer": "❌ **Service Temporarily Unavailable**\n\nBoth primary (Gemini) and fallback (Ollama) models are currently unavailable. Please try again in a few minutes.",
                        "sources": []
                    }
            elif _is_resource_exhausted_error(model_err):
                logger.error(f"Gemini quota exhausted and fallback disabled: {model_err}")
                return {
                    "answer": "❌ **API Quota Exhausted**\n\nGemini API quota has been reached. Please try again later or enable local fallback.",
                    "sources": []
                }
            else:
                raise
        
        llm_time = time.time() - llm_start
        
        # Step 7: Response normalization and intelligent source extraction
        answer_text = _normalize_llm_text(response)
        
        # Extract sources that were actually relevant to the response
        sources = _extract_relevant_sources(selected_docs, answer_text, user_question)
        
        total_time = time.time() - start_time
        logger.info(f"Query completed in {total_time:.3f}s (LLM: {llm_time:.3f}s, {len(sources)} sources)")
        
        return {"answer": answer_text, "sources": sources}
    
    except Exception as e:
        logger.exception("Unexpected error in query_pagie")
        return {
            "answer": f"❌ **Error Processing Query**\n\nAn unexpected error occurred: {str(e)}\n\nPlease check the logs and try again.",
            "sources": []
        }

# ---------------------------------------------------------------------------
# Performance Utilities
# ---------------------------------------------------------------------------
def warmup_models():
    """Pre-load all models to eliminate cold-start latency."""
    logger.info("Warming up models...")
    start_time = time.time()
    
    # Load all singleton instances
    _get_embedding_model()
    _get_vector_db() 
    _get_llm_model()
    _load_embedding_cache()
    
    # Test query to verify everything works
    try:
        result = query_pagie("test warmup query", k=1)
        warmup_time = time.time() - start_time
        logger.info(f"Models warmed up successfully in {warmup_time:.2f}s")
    except Exception as e:
        logger.error(f"Model warmup failed: {e}")

def get_cache_stats() -> Dict[str, Any]:
    """Get embedding cache statistics."""
    return {
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
        "hit_rate": _cache_hits / (_cache_hits + _cache_misses) if (_cache_hits + _cache_misses) > 0 else 0,
        "cached_queries": len(_embedding_cache)
    }

# ---------------------------------------------------------------------------
# Backward Compatibility
# ---------------------------------------------------------------------------
# Alias for compatibility with existing code
query_pagie_fast = query_pagie

if __name__ == "__main__":
    # Initialize cache and warm up models
    _load_embedding_cache()
    warmup_models()
    
    # Example usage
    result = query_pagie("Who is kimhour and what are his key skills?", k=6)
    print("Answer:", result["answer"])
    print("Sources:", result["sources"])
    print("Cache stats:", get_cache_stats())