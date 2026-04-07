# 🚀 Streamlit Cloud Deployment Guide (Git-Based)
## Deploy PAGie to Streamlit Cloud in 5 Easy Steps

---

## 📋 Prerequisites

- ✅ GitHub repository with your PAGie code
- ✅ Google Gemini API key ([Get it here](https://aistudio.google.com/app/apikey))
- ✅ Local ChromaDB with indexed CV data (run sync locally first)

---

## 🎯 Quick Deployment Steps

### **Step 1: Package Your ChromaDB for Git**

Run the packaging script to prepare your ChromaDB:

```bash
cd "/home/hour/Documents/CADT/Y3 T2/Data Science/pagie_project"

# Run the packaging script
./scripts/package_chromadb.sh
```

This will:
- ✅ Create a backup archive (for safety)
- ✅ Copy `chroma_db/` to `data/chromadb_prebuilt/chroma_db/`
- ✅ Prepare it for git commit

---

### **Step 2: Commit ChromaDB to Git**

```bash
# Add the pre-built ChromaDB to git
git add data/chromadb_prebuilt/

# Check what's being added (should show chroma_db files)
git status

# Commit and push
git commit -m "Add pre-built ChromaDB for Streamlit Cloud deployment"
git push origin main
```

**⚠️ Important:** Check the size before committing:
```bash
du -sh data/chromadb_prebuilt/chroma_db
```

- **< 100MB**: ✅ Safe to commit to GitHub
- **> 100MB**: ❌ Too large - you'll need Git LFS or GCS (we'll do this later)

---

### **Step 3: Create `.gitignore` Rule (Keep Local DB Separate)**

Make sure your `.gitignore` has this:

```bash
# Add to .gitignore to prevent local chroma_db from being committed
chroma_db/
!data/chromadb_prebuilt/chroma_db/
```

This ensures:
- ✅ Local `./chroma_db/` is ignored (not committed)
- ✅ Pre-built `./data/chromadb_prebuilt/chroma_db/` IS committed

---

### **Step 4: Deploy to Streamlit Cloud**

1. **Go to:** https://share.streamlit.io/

2. **Sign in** with your GitHub account

3. **Click "New app"**

4. **Configure:**
   - **Repository:** `YourUsername/pagie_project`
   - **Branch:** `main`
   - **Main file path:** `app.py`

5. **Click "Advanced settings"** and add secrets:

```toml
# Copy this to Streamlit Cloud Secrets section
GOOGLE_API_KEY = "your-actual-gemini-api-key-here"
APP_MODE = "prod"
```

6. **Click "Deploy"** 🚀

---

### **Step 5: Wait & Test**

The deployment takes 2-3 minutes:

1. **Watch the logs** for these messages:
   ```
   🌍 Environment: cloud | ChromaDB path: /tmp/chroma_db
   📦 Copying pre-built ChromaDB from ./data/chromadb_prebuilt/chroma_db...
   ✅ Pre-built ChromaDB copied successfully!
   ✅ Connected to ChromaDB with 920 chunks
   ```

2. **Once deployed**, test with a query:
   ```
   "Who has Python experience?"
   ```

3. **Check the sidebar** - it should show:
   ```
   📊 Chunks Indexed: 920
   ✅ Ready to answer questions
   ```

---

## 🎓 For Your Teacher Presentation

When explaining the deployment, you can say:

> "For deployment to Streamlit Cloud, I packaged the vector database as part of the repository. The application automatically detects if it's running in the cloud vs. locally and uses the appropriate file paths. On Streamlit Cloud, it uses `/tmp` which is writable, and copies the pre-built ChromaDB on first startup. This ensures the demo works reliably during the presentation without requiring external API calls or cloud storage setup."

---

## 🐛 Troubleshooting

### **Error: "No CV Data Available"**

**Cause:** ChromaDB wasn't copied from pre-built location

**Fix:**
1. Check if `data/chromadb_prebuilt/chroma_db/` exists in your repo
2. Check Streamlit logs for copy errors
3. Re-run `./scripts/package_chromadb.sh` and re-deploy

---

### **Error: "Collection [UUID] not found"**

**Cause:** Old collection ID mismatch (already fixed in latest code!)

**Fix:** Already handled! The code now:
- ✅ Uses explicit collection name: `"pagie_cv_collection"`
- ✅ Has error handling for collection issues
- ✅ Shows helpful error messages

---

### **Deployment is slow / times out**

**Cause:** ChromaDB is too large (> 100MB)

**Solutions:**
1. **Reduce CV count** - only package 20-30 sample CVs instead of 100+
2. **Use Git LFS** (Large File Storage):
   ```bash
   git lfs install
   git lfs track "data/chromadb_prebuilt/chroma_db/*"
   git add .gitattributes
   git commit -m "Track ChromaDB with Git LFS"
   ```
3. **Use GCS** (implement later when needed)

---

### **Check ChromaDB was copied correctly**

Add this temporary code to your `app.py` sidebar:

```python
import os
from pathlib import Path

st.sidebar.markdown("### 🔍 Debug Info")

# Check if pre-built exists in repo
prebuilt_path = Path("./data/chromadb_prebuilt/chroma_db")
if prebuilt_path.exists():
    file_count = len(list(prebuilt_path.rglob("*")))
    st.sidebar.success(f"✅ Pre-built DB: {file_count} files")
else:
    st.sidebar.error("❌ Pre-built DB not found")

# Check if copied to /tmp
import streamlit as st
from rag_pipeline import CHROMA_DB_PATH, IS_CLOUD_DEPLOYMENT
tmp_path = Path(CHROMA_DB_PATH)
if tmp_path.exists():
    file_count = len(list(tmp_path.rglob("*")))
    st.sidebar.success(f"✅ Active DB: {file_count} files")
else:
    st.sidebar.error("❌ Active DB not found")

st.sidebar.info(f"Environment: {'Cloud' if IS_CLOUD_DEPLOYMENT else 'Local'}")
```

---

## 📊 Environment Detection Summary

Your app now automatically detects the environment:

| Environment | ChromaDB Path | Source |
|------------|---------------|---------|
| **Local** (`app_local.py`) | `./chroma_db` | Local sync |
| **Cloud** (`app.py` deployed) | `/tmp/chroma_db` | Copied from `data/chromadb_prebuilt/` |
| **Local testing** (`app.py` local) | `./chroma_db` | Local sync |

**Detection logic:**
```python
IS_CLOUD = (
    STREAMLIT_SHARING_MODE="true" OR
    STREAMLIT_CLOUD="true" OR
    /mount/src exists
) AND NOT FORCE_LOCAL_MODE
```

**Force local mode** (for testing):
```bash
FORCE_LOCAL_MODE=true streamlit run app.py
```

---

## ✅ Deployment Checklist

Before deploying, verify:

- [ ] Local ChromaDB has data: `ls -la chroma_db/` (should show files)
- [ ] Packaged ChromaDB: `ls -la data/chromadb_prebuilt/chroma_db/` (should show files)
- [ ] Committed to git: `git log --oneline | head -3` (should see "Add pre-built ChromaDB")
- [ ] Pushed to GitHub: `git status` (should say "up to date")
- [ ] `.gitignore` excludes `chroma_db/` but not `data/chromadb_prebuilt/`
- [ ] Gemini API key ready for Streamlit secrets

---

## 🎉 Success Indicators

After deployment, you should see:

1. **In Streamlit Cloud logs:**
   ```
   ✅ Pre-built ChromaDB copied successfully!
   ✅ Connected to ChromaDB with XXX chunks
   ```

2. **In the app sidebar:**
   ```
   📊 Chunks Indexed: XXX
   ✅ Status: Ready
   ```

3. **Test query works:**
   ```
   User: "Who has Python experience?"
   PAGie: "Based on the CVs, here are 3 candidates..."
   ```

---

## 🔄 Updating ChromaDB After Deployment

If you add new CVs locally:

1. **Re-sync locally:**
   ```bash
   python sync_data.py
   ```

2. **Re-package:**
   ```bash
   ./scripts/package_chromadb.sh
   ```

3. **Re-deploy:**
   ```bash
   git add data/chromadb_prebuilt/
   git commit -m "Update ChromaDB with new CVs"
   git push
   ```

Streamlit Cloud will auto-redeploy when it detects the push!

---

## 💡 Next Steps (After Presentation)

- [ ] Implement Google Cloud Storage for production persistence
- [ ] Add file upload feature (let users upload CVs directly in the app)
- [ ] Set up CI/CD for automatic rebuilds
- [ ] Add authentication for production use

---

**Ready to deploy? Run the package script and let's go! 🚀**

```bash
./scripts/package_chromadb.sh
```
