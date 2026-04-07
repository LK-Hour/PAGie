# 🚨 Streamlit Cloud Deployment - Troubleshooting Guide

## ❌ Error: Collection [UUID] Not Found

### **Problem**
```
Error: Collection [8d2c9528-6a2e-4dfa-b05d-31bf23202152]
```

This error occurs when ChromaDB tries to reference a collection that doesn't exist in the cloud deployment.

### **Root Cause**
- **Local development**: Your ChromaDB has collections with specific UUIDs
- **Streamlit Cloud**: Starts with an EMPTY `/tmp/chroma_db` directory on each deployment
- **Mismatch**: Code references old collection IDs that don't exist in the fresh deployment

---

## ✅ SOLUTION 1: Add Pre-Built ChromaDB to Repository (Recommended)

### **Step 1: Prepare ChromaDB for Upload**

On your local machine:

```bash
cd "/home/hour/Documents/CADT/Y3 T2/Data Science/pagie_project"

# Create a compressed archive of your ChromaDB
tar -czf chromadb_backup.tar.gz chroma_db/

# Check the size (should be < 100MB for GitHub)
ls -lh chromadb_backup.tar.gz
```

### **Step 2: Add to Repository**

```bash
# Move to a committed location
mkdir -p data/chromadb_prebuilt
tar -xzf chromadb_backup.tar.gz -C data/chromadb_prebuilt/

# Add to git
git add data/chromadb_prebuilt/
git commit -m "Add pre-built ChromaDB for cloud deployment"
git push
```

### **Step 3: Update `gcs_sync.py`**

Modify `ensure_chromadb_synced()` to use the pre-built DB if `/tmp/chroma_db` is empty:

```python
def ensure_chromadb_synced():
    """
    Ensure ChromaDB is synced from cloud on first run.
    If GCS is disabled, copy from pre-built backup.
    """
    if not CHROMA_DB_PATH.exists() or not list(CHROMA_DB_PATH.glob("*")):
        if GCS_ENABLED:
            logger.info("ChromaDB not found locally - syncing from GCS...")
            sync_chromadb_from_cloud()
        else:
            # Fallback: Copy from pre-built ChromaDB in repository
            logger.info("ChromaDB not found - using pre-built database...")
            prebuilt_path = Path("./data/chromadb_prebuilt/chroma_db")
            if prebuilt_path.exists():
                import shutil
                shutil.copytree(prebuilt_path, CHROMA_DB_PATH, dirs_exist_ok=True)
                logger.info("Pre-built ChromaDB copied successfully")
            else:
                logger.warning("No pre-built ChromaDB found - will start with empty DB")
```

---

## ✅ SOLUTION 2: Use Google Cloud Storage (For Production)

### **Step 1: Set Up GCS Bucket**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new bucket (e.g., `pagie-chromadb-prod`)
3. Upload your local `chroma_db/` folder to the bucket

### **Step 2: Upload ChromaDB from Local**

```bash
# Install GCS dependencies
pip install google-cloud-storage tenacity

# Upload your ChromaDB
python gcs_sync.py --upload
```

### **Step 3: Configure Streamlit Secrets**

In Streamlit Cloud dashboard, add these secrets:

```toml
# .streamlit/secrets.toml (on Streamlit Cloud)
GOOGLE_API_KEY = "your-gemini-api-key"
GCS_ENABLED = "true"
GCS_BUCKET_NAME = "pagie-chromadb-prod"
GCS_CREDENTIALS_JSON = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
'''
```

### **Step 4: Deploy to Streamlit Cloud**

The app will automatically download ChromaDB from GCS on first run.

---

## ✅ SOLUTION 3: Rebuild ChromaDB on Cloud (Simplest but Slowest)

### **Option A: Upload CV Files to Repository**

1. Commit your CV files to the repo:
   ```bash
   git add data/drive/*.pdf
   git commit -m "Add CV files for cloud deployment"
   git push
   ```

2. Add a rebuild button in your Streamlit app:
   ```python
   if st.sidebar.button("🔄 Rebuild Knowledge Base"):
       # Re-run data_science_eda.py to rebuild ChromaDB
       rebuild_chromadb()
   ```

### **Option B: Manual Sync on First Deployment**

Skip GCS and just show a warning:

```python
if chunk_count == 0:
    st.warning("⚠️ Knowledge base is empty. Please run data sync first.")
    st.stop()
```

---

## 🔧 QUICK FIX: Updated Code (Already Applied)

I've already updated your `rag_pipeline.py` with:

1. **Explicit collection name**: 
   ```python
   Chroma(collection_name="pagie_cv_collection")
   ```

2. **Error handling** for collection issues:
   ```python
   try:
       _vector_db_instance = Chroma(...)
   except Exception as e:
       logger.warning(f"Failed to connect: {e}")
       # Create new collection
   ```

3. **Empty DB check** in `query_pagie()`:
   ```python
   if chunk_count == 0:
       return {
           "answer": "⚠️ No CV Data Available...",
           "sources": []
       }
   ```

---

## 📋 CHECKLIST FOR STREAMLIT CLOUD DEPLOYMENT

### Before Deploying:
- [ ] Choose a solution: Pre-built DB, GCS, or rebuild on cloud
- [ ] Update `.streamlit/secrets.toml` with `GOOGLE_API_KEY`
- [ ] If using GCS: Set up bucket and add credentials to secrets
- [ ] If using pre-built: Commit ChromaDB to repository (check size < 100MB)
- [ ] Test locally with `FORCE_LOCAL_MODE=false` to simulate cloud environment

### After Deploying:
- [ ] Check Streamlit Cloud logs for ChromaDB connection messages
- [ ] Test a query to verify data is loaded
- [ ] Check system status in sidebar (should show chunk count > 0)

---

## 🐛 DEBUGGING TIPS

### Check ChromaDB Status
Add this to your Streamlit sidebar:

```python
try:
    from rag_pipeline import _get_vector_db
    vector_db = _get_vector_db()
    chunk_count = vector_db._collection.count()
    st.sidebar.metric("📊 Chunks Indexed", chunk_count)
    
    if chunk_count == 0:
        st.sidebar.error("❌ Database is empty!")
    else:
        st.sidebar.success(f"✅ {chunk_count} chunks ready")
except Exception as e:
    st.sidebar.error(f"❌ ChromaDB Error: {e}")
```

### View Logs
In Streamlit Cloud:
1. Click "Manage app" → "Logs"
2. Look for these messages:
   - `"ChromaDB not found locally - syncing from GCS..."`
   - `"Connected to ChromaDB with X chunks"`
   - Any error messages about collections

---

## 🚀 RECOMMENDED SOLUTION FOR YOUR PRESENTATION

**For your teacher presentation, I recommend SOLUTION 1 (Pre-built DB):**

**Why?**
- ✅ Fastest deployment (no API setup needed)
- ✅ Works offline (no GCS dependencies)
- ✅ Reliable (data is guaranteed to be there)
- ✅ Simple to explain to your professor

**Steps:**
1. Compress your local `chroma_db/` 
2. Add it to the repository under `data/chromadb_prebuilt/`
3. Update `gcs_sync.py` to copy from pre-built on first run
4. Deploy to Streamlit Cloud

**Demo talking point:**
> "For deployment, I pre-built the vector database locally and included it in the repository. In production, you'd use cloud storage like GCS, but for this academic demo, embedding the database ensures reliability during the presentation."

---

## 📞 NEED HELP?

If you're still stuck:
1. Check the Streamlit Cloud logs (copy/paste the error)
2. Verify your `CHROMA_DB_PATH` is writable (`/tmp/chroma_db` on cloud)
3. Confirm your local `chroma_db/` folder has data: `ls -la chroma_db/`
4. Test locally with cloud settings: `FORCE_LOCAL_MODE=false streamlit run app.py`

---

Let me know which solution you want to implement and I'll help you set it up! 🚀
