# ChromaDB Collection Name Fix

## Issue
The PAGie Streamlit sidebar was showing **0 chunks** even though ChromaDB contained 16 embeddings.

## Root Cause
**Collection Name Mismatch:**
- `data_science_eda.py` creates ChromaDB with default collection name: `"langchain"`
- `rag_pipeline.py` and `rag_pipeline_local.py` were looking for: `"pagie_cv_collection"`

## Investigation Steps
1. Verified ChromaDB exists at `./chroma_db/chroma.sqlite3` (384 KB)
2. Checked SQLite database structure - found 16 embeddings in `embeddings` table
3. Queried collection names: Found `"langchain"` collection, not `"pagie_cv_collection"`
4. Identified mismatch in collection names

## Solution
Removed explicit `collection_name` parameter from Chroma initialization to use the default `"langchain"` name.

### Files Modified

#### 1. `rag_pipeline_local.py`
**Before:**
```python
_vector_db_instance = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=embedding_model,
    collection_name="pagie_cv_collection"  # ❌ Wrong
)
```

**After:**
```python
_vector_db_instance = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=embedding_model
    # ✅ Uses default "langchain" collection
)
```

#### 2. `rag_pipeline.py`
Same fix applied to maintain consistency across both cloud and local versions.

## Verification Results

### Test 1: Standalone Pipeline Test
```bash
$ python3 test_script.py
Status: Connected (16 chunks)
Total chunks: 16
Environment: local
✅ SUCCESS
```

### Test 2: Sidebar Integration Test
```bash
✓ get_db_stats() called successfully
  - Status: Connected (16 chunks)
  - Total chunks: 16
✓ get_cache_stats() called successfully
✅ SUCCESS: Sidebar will now show 16 chunks!
```

### Test 3: Main Pipeline Test
```bash
Status: Connected (16 chunks)
Total chunks: 16
✅ Main pipeline also fixed!
```

## Impact
- ✅ Sidebar now correctly displays chunk count: **16 chunks**
- ✅ Both local and cloud pipelines work correctly
- ✅ No data loss - all existing embeddings preserved
- ✅ No need to rebuild ChromaDB

## Future Prevention
To avoid this issue in the future:
1. Always use ChromaDB's default collection name, OR
2. Explicitly set the same collection name in both `data_science_eda.py` and the pipeline files

## Related Files
- `rag_pipeline.py` - Main cloud/local pipeline (FIXED)
- `rag_pipeline_local.py` - Local-only pipeline (FIXED)
- `data_science_eda.py` - Creates ChromaDB with default collection name (unchanged)
- `ui/components/sidebar_local.py` - Displays chunk count (no changes needed)

---
**Fixed:** 2026-04-08
**Issue Type:** Configuration mismatch
**Severity:** Medium (feature not working, but no data loss)
**Resolution:** Collection name alignment
