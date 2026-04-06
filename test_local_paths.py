#!/usr/bin/env python3
"""
Test script to verify app_local.py uses correct local paths
"""

import os
import sys

def test_local_mode():
    """Test that FORCE_LOCAL_MODE correctly sets local paths"""
    
    print("\n" + "="*70)
    print("🧪 Testing PAGie Local vs Cloud Path Configuration")
    print("="*70)
    
    # Test 1: Force Local Mode
    print("\n📍 Test 1: FORCE_LOCAL_MODE = true")
    print("-" * 70)
    
    os.environ['FORCE_LOCAL_MODE'] = 'true'
    
    # Clear any cached imports
    for module in list(sys.modules.keys()):
        if 'rag_pipeline' in module or 'data_science_eda' in module:
            del sys.modules[module]
    
    from rag_pipeline import CHROMA_DB_PATH, EMBEDDING_CACHE_PATH
    from data_science_eda import CHROMA_DB_DIR, ASSETS_DIR
    
    print(f"  ChromaDB (rag):       {CHROMA_DB_PATH}")
    print(f"  ChromaDB (eda):       {CHROMA_DB_DIR}")
    print(f"  Embedding Cache:      {EMBEDDING_CACHE_PATH}")
    print(f"  Assets:               {ASSETS_DIR}")
    
    test1_pass = all([
        str(CHROMA_DB_PATH).startswith('./'),
        str(CHROMA_DB_DIR).startswith('./'),
        str(EMBEDDING_CACHE_PATH).startswith('./'),
        not str(ASSETS_DIR).startswith('/tmp')
    ])
    
    if test1_pass:
        print("  ✅ PASS: All paths are local")
    else:
        print("  ❌ FAIL: Some paths are not local")
    
    # Test 2: Cloud Auto-Detection (simulated)
    print("\n📍 Test 2: FORCE_LOCAL_MODE = false (Cloud detection)")
    print("-" * 70)
    
    os.environ['FORCE_LOCAL_MODE'] = 'false'
    
    # Clear cached imports again
    for module in list(sys.modules.keys()):
        if 'rag_pipeline' in module or 'data_science_eda' in module:
            del sys.modules[module]
    
    from rag_pipeline import CHROMA_DB_PATH as CLOUD_CHROMA
    from data_science_eda import CHROMA_DB_DIR as CLOUD_CHROMA_DIR
    
    print(f"  ChromaDB (rag):       {CLOUD_CHROMA}")
    print(f"  ChromaDB (eda):       {CLOUD_CHROMA_DIR}")
    
    # When streamlit is imported, it might have st.secrets
    # which triggers cloud path detection
    import streamlit as st
    has_secrets = hasattr(st, 'secrets')
    
    if has_secrets:
        # Should use /tmp paths
        test2_pass = str(CLOUD_CHROMA).startswith('/tmp')
        if test2_pass:
            print("  ✅ PASS: Cloud detection works (using /tmp)")
        else:
            print("  ⚠️  NOTE: st.secrets found but not using /tmp")
    else:
        # Should use local paths
        test2_pass = str(CLOUD_CHROMA).startswith('./')
        if test2_pass:
            print("  ✅ PASS: Local environment detected correctly")
        else:
            print("  ❌ FAIL: Should use local paths when st.secrets not found")
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    print(f"  Test 1 (Force Local):      {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"  Test 2 (Auto Detection):   {'✅ PASS' if test2_pass else '⚠️ SEE NOTE'}")
    
    print("\n💡 Key Points:")
    print("  • app_local.py sets FORCE_LOCAL_MODE=true automatically")
    print("  • app.py lets auto-detection work (cloud vs local)")
    print("  • Local paths: ./chroma_db, ./cache, ./assets")
    print("  • Cloud paths: /tmp/chroma_db, /tmp/cache, /tmp/assets")
    
    print("\n" + "="*70)
    
    return test1_pass and test2_pass

if __name__ == "__main__":
    try:
        success = test_local_mode()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
