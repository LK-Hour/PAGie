# Quick Reference: app.py vs app_local.py

## Which App Should I Run?

```bash
# 🏠 LOCAL DEVELOPMENT (recommended)
streamlit run app_local.py

# ☁️ CLOUD DEPLOYMENT (Streamlit Cloud)
# Just push to GitHub - uses app.py automatically
```

## Path Configuration Summary

| Component | app_local.py | app.py (Local) | app.py (Cloud) |
|-----------|--------------|----------------|----------------|
| **ChromaDB** | `./chroma_db` | `./chroma_db` | `/tmp/chroma_db` |
| **Embedding Cache** | `./cache/` | `./cache/` | `/tmp/cache/` |
| **Assets (EDA)** | `./assets/` | `./assets/` | `/tmp/assets/` |
| **CV Files** | Google Drive OAuth | Google Drive OAuth | Repository files |
| **Environment Var** | `FORCE_LOCAL_MODE=true` | Auto-detect | Auto-detect |

## How It Works

### app_local.py
```python
# Sets this BEFORE any imports
os.environ["FORCE_LOCAL_MODE"] = "true"

# This forces rag_pipeline.py and data_science_eda.py to use:
CHROMA_DB_PATH = "./chroma_db"        # Not /tmp/chroma_db
EMBEDDING_CACHE_PATH = "./cache/..."  # Not /tmp/cache/...
ASSETS_DIR = "./assets"                # Not /tmp/assets
```

### app.py
```python
# No FORCE_LOCAL_MODE set
# Auto-detection runs in rag_pipeline.py and data_science_eda.py:

if hasattr(st, 'secrets'):
    # On Streamlit Cloud
    CHROMA_DB_PATH = "/tmp/chroma_db"
else:
    # On local machine
    CHROMA_DB_PATH = "./chroma_db"
```

## Testing

```bash
# Test path configuration
python test_local_paths.py

# Run local version
./run_local.sh
# OR
streamlit run app_local.py

# Run cloud-ready version locally (for testing)
streamlit run app.py
```

## Key Differences

| Feature | app_local.py | app.py |
|---------|-------------|--------|
| **Purpose** | Local dev only | Cloud + local |
| **Code Complexity** | Simple | Has cloud logic |
| **Path Logic** | Force local | Auto-detect |
| **Best For** | Development | Deployment |
| **CV Sync** | Google Drive OAuth | Repository files on cloud |
| **GCS Integration** | No | Optional |

## Common Issues

### "ChromaDB not persistent on cloud"
**Cause:** Using `/tmp` which is ephemeral  
**Solution:** Configure GCS in Streamlit Cloud secrets

### "app_local.py using /tmp paths"
**Cause:** FORCE_LOCAL_MODE not set early enough  
**Solution:** Already fixed - set in `app_local.py` before imports

### "Google Drive sync fails on cloud"
**Cause:** OAuth requires browser (not available on serverless)  
**Solution:** Use `app.py` which uses repository CV files

## File Structure

```
pagie_project/
├── app.py              ← Use for Streamlit Cloud deployment
├── app_local.py        ← Use for local development  
├── run_local.sh        ← Quick launcher for local mode
├── test_local_paths.py ← Verify path configuration
│
├── rag_pipeline.py          ← Has FORCE_LOCAL_MODE logic
├── data_science_eda.py      ← Has FORCE_LOCAL_MODE logic
│
└── ui/components/
    ├── sidebar.py           ← Cloud-aware (for app.py)
    └── sidebar_local.py     ← Local-only (for app_local.py)
```

## Development Workflow

```bash
# 1. Clone repository
git clone <repo-url>
cd pagie_project

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
nano .env  # Add your API keys

# 4. Run local version
streamlit run app_local.py

# 5. (Optional) Test cloud version locally
streamlit run app.py
```

## Deployment to Streamlit Cloud

```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for deployment"
git push

# 2. Go to share.streamlit.io
# 3. Connect repo, set main file to: app.py
# 4. Add secrets (GOOGLE_API_KEY, etc.)
# 5. Deploy!
```

---

**TL;DR:**
- **Local dev?** → `streamlit run app_local.py` (forces local paths)
- **Deploy?** → Push to GitHub, use `app.py` (auto-detects cloud)
- **Need help?** → `python test_local_paths.py` to verify paths
