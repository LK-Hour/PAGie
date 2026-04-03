#!/usr/bin/env python3
"""
optimize_performance.py — Performance Analysis & Optimization for PAGie
======================================================================
Identifies bottlenecks and applies optimizations to improve response time.
"""

import os
import time
import functools
from typing import Dict, Any, Optional
from pathlib import Path

# Global caches for performance
_model_cache: Dict[str, Any] = {}
_db_cache: Optional[Any] = None

def time_operation(operation_name: str):
    """Decorator to measure execution time of functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            print(f"⏱️ {operation_name}: {duration:.2f}s")
            return result
        return wrapper
    return decorator

def analyze_current_performance():
    """Analyze current performance bottlenecks."""
    print("🔍 PAGie Performance Analysis")
    print("=" * 50)
    
    # Check vector database size
    try:
        from rag_pipeline import get_vector_db
        db = get_vector_db()
        count = db._collection.count()
        print(f"📦 Vector DB size: {count:,} chunks")
        
        if count > 10000:
            print("⚠️ Large vector DB detected - consider chunk optimization")
        elif count < 100:
            print("⚠️ Small vector DB - may need more data")
        else:
            print("✅ Vector DB size looks reasonable")
            
    except Exception as e:
        print(f"❌ Vector DB connection failed: {e}")
        return
    
    # Test query performance
    test_queries = [
        "What programming skills are mentioned?",
        "What is the educational background?", 
        "Any machine learning experience?"
    ]
    
    print(f"\n🏃 Testing {len(test_queries)} sample queries...")
    
    from rag_pipeline import query_pagie
    
    total_time = 0
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query[:40]}...")
        
        start = time.time()
        try:
            result = query_pagie(query)
            end = time.time()
            query_time = end - start
            total_time += query_time
            
            print(f"  ✅ Completed in {query_time:.2f}s")
            print(f"  📝 Answer length: {len(result.get('answer', ''))}")
            print(f"  📄 Sources found: {len(result.get('sources', []))}")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    avg_time = total_time / len(test_queries)
    print(f"\n📊 Performance Summary:")
    print(f"  • Average query time: {avg_time:.2f}s")
    print(f"  • Total test time: {total_time:.2f}s")
    
    # Performance recommendations
    print(f"\n💡 Performance Recommendations:")
    if avg_time > 10:
        print("  🔴 CRITICAL: Very slow responses (>10s)")
        print("     → Check internet connection to Gemini API")
        print("     → Consider using local LLM for development")
    elif avg_time > 5:
        print("  🟡 SLOW: Above acceptable range (>5s)")
        print("     → Optimize context size and retrieval")
    else:
        print("  🟢 GOOD: Acceptable response time (<5s)")
    
    return {
        "avg_time": avg_time,
        "total_time": total_time,
        "db_size": count
    }

def optimize_rag_pipeline():
    """Apply immediate optimizations to existing pipeline."""
    print("\n🛠️ Applying Performance Optimizations")
    print("=" * 50)
    
    # 1. Check environment variables
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ No .env file found - create one for API keys")
        return
    
    # 2. Suggest environment optimizations
    optimizations = {
        "MAX_CONTEXT_CHARS": "8000",  # Reduce from 10000
        "RETRIEVAL_MULTIPLIER": "2",   # Reduce from 3  
        "MAX_CANDIDATES": "30",        # Reduce from 50
        "GEMINI_MODEL": "gemini-1.5-flash-latest"  # Faster model
    }
    
    print("📝 Recommended .env optimizations:")
    for key, value in optimizations.items():
        print(f"  {key}={value}")
    
    # 3. Create optimized config
    config_content = """# Performance Optimized Configuration for PAGie
# Add these to your .env file:

# Reduce context size for faster processing
MAX_CONTEXT_CHARS=8000

# Reduce retrieval candidates 
RETRIEVAL_MULTIPLIER=2
MAX_CANDIDATES=30

# Use fastest Gemini model
GEMINI_MODEL=gemini-1.5-flash-latest

# Enable local development mode for testing
APP_MODE=dev
"""
    
    with open("performance_config.env", "w") as f:
        f.write(config_content)
    
    print(f"\n✅ Created performance_config.env")
    print("   Copy relevant settings to your .env file")

def create_cached_wrapper():
    """Create a cached version of the query function."""
    cache_file = Path("./cache/query_cache.txt")
    cache_file.parent.mkdir(exist_ok=True)
    
    wrapper_code = '''
# Add this to your rag_pipeline.py for caching:

import functools
import hashlib
import json
import os
from pathlib import Path

_query_cache = {}
CACHE_FILE = Path("./cache/query_cache.json")

def load_cache():
    """Load cached results from disk."""
    global _query_cache
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                _query_cache = json.load(f)
        except:
            _query_cache = {}

def save_cache():
    """Save cache to disk."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(_query_cache, f, indent=2)

def cached_query_pagie(user_question: str, k: int = 8):
    """Cached version of query_pagie for repeated questions."""
    # Create cache key
    cache_key = hashlib.md5(f"{user_question}|{k}".encode()).hexdigest()
    
    # Check cache first
    if cache_key in _query_cache:
        print("🚀 Cache hit!")
        return _query_cache[cache_key]
    
    # Call original function
    result = query_pagie(user_question, k)
    
    # Cache result
    _query_cache[cache_key] = result
    save_cache()
    
    return result

# Initialize cache on import
load_cache()
'''
    
    with open("cache_wrapper.py", "w") as f:
        f.write(wrapper_code)
    
    print("📦 Created cache_wrapper.py - add to rag_pipeline.py for caching")

def main():
    """Run complete performance analysis and optimization."""
    print("🚀 PAGie Performance Optimization Suite")
    print("="*50)
    
    # Step 1: Analyze current performance
    stats = analyze_current_performance()
    
    if not stats:
        print("❌ Cannot proceed without working RAG pipeline")
        return 1
    
    # Step 2: Apply optimizations
    optimize_rag_pipeline()
    
    # Step 3: Create caching tools
    create_cached_wrapper()
    
    # Step 4: Final recommendations
    print(f"\n🎯 Next Steps for {stats['avg_time']:.1f}s → <3s performance:")
    print("  1. Copy settings from performance_config.env to .env")
    print("  2. Switch to app_optimized.py if available") 
    print("  3. Add caching from cache_wrapper.py")
    print("  4. Consider local LLM for development (ollama)")
    print("  5. Restart Streamlit: streamlit run app.py")
    
    return 0

if __name__ == "__main__":
    exit(main())