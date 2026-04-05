# 🚀 Quick Streamlit Cloud Deployment Checklist

Follow these steps to deploy PAGie to Streamlit Cloud in ~5 minutes!

---

## ✅ Pre-Deployment (Already Done!)

- [x] Code pushed to GitHub: `https://github.com/LK-Hour/PAGie.git`
- [x] Branch: `cv_focus`
- [x] Main file: `app.py`
- [x] Requirements file: `requirements.txt`
- [x] Streamlit config: `.streamlit/config.toml`

---

## 📝 Step 1: Get Your Google API Key

1. Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**
2. Click **"Create API Key"** (or use existing one)
3. Copy the key (starts with `AIza...`)
4. **Save it somewhere safe** - you'll need it in Step 3

---

## 🌐 Step 2: Deploy on Streamlit Cloud

1. Visit: **https://share.streamlit.io/**
2. Sign in with your GitHub account (if not already signed in)
3. Click **"New app"** (or **"Create app"**)
4. Configure deployment:
   - **Repository**: `LK-Hour/PAGie`
   - **Branch**: `cv_focus`
   - **Main file path**: `app.py`
   - **App URL** (optional): Choose a custom subdomain like `pagie-cv-analyzer`

---

## 🔐 Step 3: Add Secrets

**IMPORTANT**: Before clicking "Deploy", click **"Advanced settings"** → **"Secrets"**

Paste this configuration (replace with your actual API key):

```toml
# Google Gemini API Key (REQUIRED)
GOOGLE_API_KEY = "AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Google Drive Folder ID (where your CV files are stored)
# Get this from your Drive folder URL: https://drive.google.com/drive/folders/YOUR_FOLDER_ID
GOOGLE_DRIVE_FOLDER_ID = "your-folder-id-here"

# Optional: Runtime mode (defaults to "prod" if not set)
APP_MODE = "prod"

# Optional: Gemini model (defaults to gemini-1.5-flash-latest if not set)
GEMINI_MODEL = "gemini-1.5-flash-latest"
```

**Required**:
- `GOOGLE_API_KEY` - Your Google AI Studio API key

**Recommended**:
- `GOOGLE_DRIVE_FOLDER_ID` - So the app can sync CV files from Google Drive

**Optional (GCS - for later)**:
- `GCS_ENABLED` - Set to `"false"` for now (or omit entirely)

---

## 🎉 Step 4: Deploy!

1. Click **"Deploy"**
2. Wait 3-5 minutes for deployment
3. Watch the logs for any errors
4. Your app will be live at: `https://your-app-name.streamlit.app`

---

## ✅ Post-Deployment Verification

### Check the Logs
Look for these success messages:
```
INFO - Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
INFO - Embedding model loaded in X.XX seconds
INFO - PAGie models warmed up successfully
```

### Test the App
1. Open your app URL
2. You should see the PAGie chat interface
3. Try a test question like: "What is PAGie?"
4. Verify the response looks correct

---

## ⚠️ Known Limitations (Without GCS)

Since you're deploying without GCS for now:

1. **ChromaDB is not persistent**
   - Your vector database will be empty on first deploy
   - It will reset on app restarts (when Streamlit recycles the container)
   - **Solution**: You can still use the app, but you'll need to rebuild ChromaDB after restarts

2. **No Google Drive sync on cloud**
   - The sync_data.py script requires OAuth token.json which isn't available in cloud
   - **Workaround**: Build ChromaDB locally and commit it to GitHub (remove from .gitignore)

### Quick Fix: Include ChromaDB in Repo

If you want your knowledge base to persist:

```bash
# On your local machine
cd "/home/hour/Documents/CADT/Y3 T2/Data Science/pagie_project"

# Remove ChromaDB from .gitignore temporarily
nano .gitignore  # Comment out the line: # /chroma_db/

# Add and commit ChromaDB
git add chroma_db/
git commit -m "Add pre-built ChromaDB for deployment"
git push origin cv_focus

# Redeploy on Streamlit Cloud (it will auto-detect changes)
```

---

## 🔧 Troubleshooting

### Issue 1: "Missing GOOGLE_API_KEY"
**Solution**: Add `GOOGLE_API_KEY` to Streamlit secrets (Step 3)

### Issue 2: App crashes on startup
**Solution**: Check logs for error messages. Common issues:
- Missing dependencies (check requirements.txt)
- Invalid API key
- Import errors

### Issue 3: "ChromaDB is empty"
**Solution**: Either:
1. Commit ChromaDB to repo (see "Quick Fix" above)
2. Set up GCS later (see `docs/GCS_DEPLOYMENT_GUIDE.md`)

### Issue 4: Slow first query
**Solution**: Normal! Embedding model loads on first query. Subsequent queries are fast (cached).

---

## 📚 Next Steps

After successful deployment:

1. **Test thoroughly**: Try various queries
2. **Monitor usage**: Check Google AI Studio quota
3. **Set up GCS (later)**: For persistent ChromaDB storage
   - Follow `docs/GCS_DEPLOYMENT_GUIDE.md`
   - Update Streamlit secrets with GCS config
   - Redeploy

---

## 🎓 Your App is Live!

Once deployed, you can:

✅ Share the URL with anyone (no login required)  
✅ Ask questions about your CV knowledge base  
✅ Update code by pushing to GitHub (auto-redeploys)  
✅ Monitor logs in Streamlit Cloud dashboard  
✅ Scale to millions of users (Streamlit handles it!)  

**App URL**: `https://your-app-name.streamlit.app`

---

## 📖 Documentation

- **Full deployment guide**: `docs/DEPLOYMENT.md`
- **GCS setup (later)**: `docs/GCS_DEPLOYMENT_GUIDE.md`
- **GCS integration summary**: `docs/GCS_INTEGRATION_SUMMARY.md`

---

**Questions?** Check the Streamlit Cloud docs or app logs!

**Ready to deploy?** Let's go! 🚀
