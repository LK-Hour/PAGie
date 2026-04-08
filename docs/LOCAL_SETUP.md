# PAGie Local Development Files

## Overview
This document describes the local-only versions of PAGie's core files, created specifically for pure local development without any cloud detection or synchronization.

## Created Files

### 1. `rag_pipeline_local.py`
**Purpose:** Local-only RAG pipeline with no cloud detection

**Key Differences from `rag_pipeline.py`:**
- ❌ No Streamlit Cloud detection (`_is_streamlit_cloud()` removed)
- ❌ No GCS sync imports or logic
- ✅ Hard-coded local paths:
  - ChromaDB: `./chroma_db`
  - Cache: `./cache/embeddings_v2.pkl`
- ✅ Environment: Always set to `"local"`
- ✅ Keeps Google Gemini 3.0 and Ollama support
- ✅ Full caching and retrieval optimization

**Usage:**
```python
from rag_pipeline_local import warmup_models, query_pagie, get_db_stats
```

---

### 2. `sync_data_local.py`
**Purpose:** Local-only ETL pipeline for Google Drive sync

**Key Differences from `sync_data.py`:**
- ❌ No cloud token detection from Streamlit secrets
- ❌ No GCS sync logic at the end of `run_sync()`
- ❌ No Notion sync (removed entirely for CV-focused workflow)
- ✅ Pure Google Drive OAuth using local `token.json`
- ✅ Local data storage: `./data/drive/`
- ✅ Local sync state: `./data/sync_state.json`
- ✅ Smart incremental sync (unchanged files skipped)

**Usage:**
```bash
python sync_data_local.py  # Run once + schedule nightly
```

Or from Python:
```python
from sync_data_local import run_sync
run_sync()
```

---

### 3. `ui/components/chat_interface_local.py`
**Purpose:** Local chat interface that uses `rag_pipeline_local`

**Key Differences from `chat_interface.py`:**
- ✅ Imports `rag_pipeline_local` instead of `rag_pipeline`
- ✅ Header shows "(Local Mode)" to indicate local development
- ✅ All other UI features remain identical

**Usage:**
```python
from ui.components.chat_interface_local import render_chat_interface
```

---

## Updated Files

### 4. `app_local.py`
**Changes:**
```python
# Before
from rag_pipeline import warmup_models, CHROMA_DB_PATH, EMBEDDING_CACHE_PATH
from ui import render_chat_interface

# After
from rag_pipeline_local import warmup_models, CHROMA_DB_PATH, EMBEDDING_CACHE_PATH
from ui.components.chat_interface_local import render_chat_interface
```

---

### 5. `ui/components/sidebar_local.py`
**Changes:**
```python
# Before
from rag_pipeline import get_cache_stats, get_db_stats
from sync_data import run_sync
import rag_pipeline

# After
from rag_pipeline_local import get_cache_stats, get_db_stats
from sync_data_local import run_sync
import rag_pipeline_local
```

---

## Architecture Comparison

### Cloud/Production Setup (`app.py`)
```
app.py
  ├── rag_pipeline.py (cloud-aware)
  ├── sync_data.py (cloud sync + GCS)
  ├── ui/components/chat_interface.py
  └── ui/components/sidebar.py
```

### Local Development Setup (`app_local.py`)
```
app_local.py
  ├── rag_pipeline_local.py (local-only)
  ├── sync_data_local.py (no GCS)
  ├── ui/components/chat_interface_local.py
  └── ui/components/sidebar_local.py
```

---

## Running PAGie Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create or update `.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
APP_MODE=dev  # or prod
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_MODEL=qwen3.5:0.8b
FORCE_LOCAL_MODE=true  # Important for local development
```

### 3. Sync CV Files from Google Drive
```bash
python sync_data_local.py
```

This will:
- Open browser for Google OAuth (first time only)
- Download CV files to `./data/drive/`
- Save sync state to `./data/sync_state.json`
- Schedule nightly sync at 02:00 AM

### 4. Build Knowledge Base
```bash
python data_science_eda.py
```

This will:
- Load CV files from `./data/drive/`
- Apply IQR filtering to clean data
- Generate embeddings
- Save to local ChromaDB (`./chroma_db/`)
- Create EDA report (`./assets/eda_report.png`)

### 5. Run Streamlit App
```bash
streamlit run app_local.py
```

Or use the shell script:
```bash
./run_local.sh
```

---

## Benefits of Local-Only Files

### 🎯 **Clarity**
- No cloud detection logic cluttering the code
- Easier to understand and debug
- Clear separation between local and cloud deployments

### 🚀 **Performance**
- No unnecessary cloud checks
- Direct path configuration
- Faster initialization

### 🔧 **Maintainability**
- Changes to local development don't affect production
- Can test new features in isolation
- Easier onboarding for new developers

### 🛡️ **Reliability**
- No accidental cloud deployments from local code
- Local paths always guaranteed
- No dependency on cloud services during development

---

## File Size Reference
- `rag_pipeline_local.py`: ~20 KB
- `sync_data_local.py`: ~14 KB
- `chat_interface_local.py`: ~5.6 KB

---

## Notes

1. **Google Drive OAuth**: Both local and cloud versions use Google Drive OAuth. The difference is:
   - Local: Uses `token.json` file
   - Cloud: Uses Streamlit secrets (`GOOGLE_DRIVE_TOKEN_JSON`)

2. **ChromaDB**: Always stored locally at `./chroma_db/` in local mode. The cloud version uses `/tmp/chroma_db` on Streamlit Cloud.

3. **Embedding Cache**: Local cache at `./cache/embeddings_v2.pkl` for faster repeated queries.

4. **Data Science EDA**: The `data_science_eda.py` file works with both setups by checking the `FORCE_LOCAL_MODE` environment variable.

5. **LLM Models**: Both setups support:
   - Google Gemini (production)
   - Ollama (local development)

---

## Troubleshooting

### Issue: "ChromaDB path does NOT exist"
**Solution:**
```bash
python data_science_eda.py  # Rebuild knowledge base
```

### Issue: "GOOGLE_DRIVE_FOLDER_ID is required"
**Solution:** Add to `.env`:
```bash
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
```

### Issue: "No CV files found"
**Solution:**
```bash
python sync_data_local.py  # Sync from Google Drive first
```

### Issue: Local paths not being used
**Solution:** Set in `.env`:
```bash
FORCE_LOCAL_MODE=true
```

---

**Last Updated:** 2026-04-08
**Created by:** GitHub Copilot CLI
**Project:** PAGie - CADT University (Group 5)
