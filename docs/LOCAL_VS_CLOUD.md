# PAGie Local vs Cloud Deployment Guide

This document explains the difference between the two app versions and when to use each.

## 📁 File Structure

```
pagie_project/
├── app.py              ← Cloud-ready version (Streamlit Cloud)
├── app_local.py        ← Local-only version (no cloud logic)
├── ui/
│   └── components/
│       ├── sidebar.py        ← Cloud-aware sidebar
│       └── sidebar_local.py  ← Local-only sidebar
```

## 🏠 Local Development: `app_local.py`

**Use this for:** Local development, testing, and running on your machine.

### Features
- ✅ **Pure local paths**: Uses `./chroma_db`, `./cache`, `./assets`
- ✅ **Google Drive OAuth**: Direct sync via `sync_data.py`
- ✅ **Ollama support**: Full local LLM support
- ✅ **No cloud detection**: Clean, simple code
- ❌ **No GCS sync**: No cloud storage integration
- ❌ **No path detection**: Always uses local paths

### Run Locally
```bash
# Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the app
streamlit run app_local.py
```

### Environment Variables (.env)
```bash
# Google Drive OAuth
GOOGLE_DRIVE_FOLDER_ID=your_folder_id

# Gemini API (fallback)
GOOGLE_API_KEY=your_gemini_key

# App Configuration
APP_MODE=dev           # Uses Ollama if available
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:7b

# Local Mode (automatically set by app_local.py)
FORCE_LOCAL_MODE=true  # Forces ./chroma_db, ./cache, ./assets
```

### Local Workflow
1. **Sync from Drive**: Click "Sync from Drive" → Authenticates with Google OAuth
2. **Rebuild KB**: Click "Rebuild KB" → Processes CVs to `./chroma_db`
3. **Chat**: Ask questions about your CVs
4. **EDA Report**: View in sidebar under "EDA Report" tab

---

## ☁️ Cloud Deployment: `app.py`

**Use this for:** Deploying to Streamlit Cloud.

### Features
- ✅ **Cloud path detection**: Auto uses `/tmp` on cloud
- ✅ **Streamlit secrets**: Uses `st.secrets` for API keys
- ✅ **Repository CV files**: Uses pre-committed `data/drive/*.pdf`
- ✅ **GCS integration** (optional): Persistent ChromaDB storage
- ✅ **Ollama fallback**: Auto-switches to Gemini on cloud
- ✅ **Environment aware**: Detects local vs cloud automatically

### Deploy to Streamlit Cloud

#### Step 1: Prepare Repository
```bash
# Commit CV files to repository (if not already done)
git add data/drive/*.pdf
git commit -m "Add CV files for cloud deployment"
git push origin cv_focus
```

#### Step 2: Configure Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set main file to: `app.py`
4. Add secrets in "Advanced settings":

```toml
# Required: Gemini API
GOOGLE_API_KEY = "your_gemini_api_key"

# Optional: GCS for ChromaDB persistence
GCS_ENABLED = "true"
GCS_BUCKET_NAME = "your-bucket-name"
GCS_CREDENTIALS_JSON = '''
{
  "type": "service_account",
  "project_id": "your-project",
  ...
}
'''
```

#### Step 3: Deploy
Click "Deploy" and wait for the app to start.

### Cloud Behavior

| Feature | Without GCS | With GCS |
|---------|-------------|----------|
| CV Files | Uses `data/drive/*.pdf` from repo | Same |
| ChromaDB | Rebuilds on container restart | Synced to GCS bucket |
| Rebuild Time | ~1-2 min on restart | ~10 sec (download from GCS) |
| Persistence | Ephemeral (`/tmp`) | Persistent (GCS) |

### Cloud Workflow
1. **First Run**: Auto-rebuilds ChromaDB from repository CV files
2. **Sync Files**: Uses repository files (no Google Drive OAuth)
3. **Rebuild KB**: Rebuilds to `/tmp/chroma_db` (with optional GCS sync)
4. **Container Restart**: ChromaDB rebuilds (unless GCS configured)

---

## 🔄 Key Differences

### Path Detection
**`app.py`** (Cloud-aware):
```python
# Auto-detects environment
if is_streamlit_cloud():
    CHROMA_DB_PATH = "/tmp/chroma_db"
else:
    CHROMA_DB_PATH = "./chroma_db"
```

**`app_local.py`** (Local-only):
```python
# Always uses local paths
CHROMA_DB_PATH = "./chroma_db"
```

### CV File Sync
**`app.py`** (Cloud-aware):
```python
from cloud_sync import sync_cv_files
result = sync_cv_files()  # Auto-detects local vs cloud
```

**`app_local.py`** (Local-only):
```python
from sync_data import run_sync
run_sync()  # Always uses Google Drive OAuth
```

### ChromaDB Persistence
**`app.py`** (Cloud-aware):
```python
from gcs_sync import ensure_chromadb_synced
ensure_chromadb_synced()  # Downloads from GCS if configured
```

**`app_local.py`** (Local-only):
```python
# No GCS sync - uses local ./chroma_db directly
```

---

## 🎯 Which One Should You Use?

### Use `app_local.py` when:
- 👨‍💻 Developing locally
- 🧪 Testing new features
- 🔒 Working with sensitive data (stays on your machine)
- ⚡ Want faster iteration (no cloud complexity)
- 🤖 Using Ollama for local LLM

### Use `app.py` when:
- 🌐 Deploying to Streamlit Cloud
- 🤝 Sharing with others via public URL
- 📱 Accessing from any device
- 💾 Need ChromaDB persistence (with GCS)
- ☁️ Using cloud-only features

---

## 🛠️ Development Workflow

```bash
# Local development
streamlit run app_local.py

# Test cloud behavior locally (optional)
export STREAMLIT_RUNTIME_ENV=cloud
streamlit run app.py

# Deploy to cloud
git push origin cv_focus
# → Auto-deploys to Streamlit Cloud
```

---

## 📊 Architecture Comparison

### Local (`app_local.py`)
```
┌──────────────┐
│  app_local   │
└──────┬───────┘
       │
       ├─→ Google Drive OAuth (sync_data.py)
       ├─→ ./chroma_db (local)
       ├─→ ./cache (local)
       ├─→ ./assets (local)
       └─→ Ollama (optional)
```

### Cloud (`app.py`)
```
┌──────────────┐
│    app.py    │
└──────┬───────┘
       │
       ├─→ data/drive/*.pdf (repository)
       ├─→ /tmp/chroma_db (ephemeral)
       ├─→ /tmp/cache (ephemeral)
       ├─→ /tmp/assets (ephemeral)
       ├─→ GCS bucket (optional, persistent)
       └─→ Gemini 3.0 (cloud LLM)
```

---

## 🐛 Troubleshooting

### Local Issues (`app_local.py`)

**Problem**: "Google Drive OAuth not working"
```bash
# Solution: Regenerate OAuth credentials
rm token.json
streamlit run app_local.py
# Click "Sync from Drive" to re-authenticate
```

**Problem**: "Ollama connection refused"
```bash
# Solution: Start Ollama service
ollama serve
# Or edit .env to use Gemini
APP_MODE=prod
```

### Cloud Issues (`app.py`)

**Problem**: "ChromaDB rebuilds on every restart"
```bash
# Solution: Configure GCS in Streamlit Cloud secrets
GCS_ENABLED = "true"
GCS_BUCKET_NAME = "your-bucket"
```

**Problem**: "No CV files found"
```bash
# Solution: Commit CV files to repository
git add data/drive/*.pdf
git commit -m "Add CV files"
git push
```

---

## 📚 Additional Resources

- **Cloud Sync Details**: See `docs/STREAMLIT_CLOUD_SYNC.md`
- **ChromaDB Persistence**: See `docs/CHROMADB_CLOUD.md`
- **Deployment Guide**: See `STREAMLIT_DEPLOY_NOW.md`

---

## 🎓 Academic Note

This dual-app architecture demonstrates:
- **Separation of Concerns**: Cloud vs local logic isolated
- **Environment Awareness**: Automatic detection and adaptation
- **Graceful Degradation**: Features adapt to capabilities
- **Code Maintainability**: Each version is simple and focused
- **Best Practices**: Clean code, clear documentation, modular design

Perfect for a university project showing real-world software engineering! 🚀
