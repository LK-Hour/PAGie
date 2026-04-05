# 🚀 Streamlit Cloud Deployment Guide

## 📚 Deployment Options

1. **[Quick Deploy (Basic)](#quick-deploy-basic)** - Deploy without persistent storage
2. **[Production Deploy with GCS](#production-deploy-with-gcs)** - Deploy with persistent ChromaDB storage (Recommended)

---

## Quick Deploy (Basic)

**⚠️ Note**: This basic deployment will lose your ChromaDB vector database on app restarts. For production use with persistent storage, see the [GCS Deployment Guide](GCS_DEPLOYMENT_GUIDE.md).

## Quick Deploy Checklist

✅ **Files Created:**
- `.streamlit/config.toml` - UI theme and server settings
- `.streamlit/secrets.toml.example` - Template for secrets
- Updated `.gitignore` to exclude secrets.toml
- Updated `rag_pipeline.py` to support Streamlit secrets

✅ **Code Changes:**
- Added Streamlit secrets support (falls back to .env for local dev)
- Works seamlessly in both local and cloud environments

---

## Production Deploy with GCS

For **production deployment** with persistent ChromaDB storage that survives app restarts:

📖 **See the complete guide**: [GCS_DEPLOYMENT_GUIDE.md](GCS_DEPLOYMENT_GUIDE.md)

**Benefits**:
- ✅ ChromaDB persists across app restarts
- ✅ 5 GB free storage on Google Cloud Storage
- ✅ Automatic sync on startup and after data updates
- ✅ Incremental sync to minimize bandwidth

**Quick overview**:
1. Create a GCS bucket in Google Cloud Console
2. Create a service account with Storage Object Admin role
3. Add GCS credentials to Streamlit secrets
4. Deploy with `GCS_ENABLED = "true"`

---

## 🌐 Deploy Now (3 Steps)

### Step 1: Get Your API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key (starts with `AIza...`)

### Step 2: Deploy on Streamlit Cloud
1. Visit: **https://share.streamlit.io/**
2. Click **"New app"**
3. Select:
   - Repository: `LK-Hour/PAGie`
   - Branch: `main`
   - Main file: `app.py`

### Step 3: Add Secrets
In the deployment settings, click **"Advanced settings" → "Secrets"** and paste:

```toml
GOOGLE_API_KEY = "AIza..."  # Your actual key
```

Click **"Deploy"** and you're live! 🎉

---

## ⚙️ Environment Variables (Optional)

You can customize behavior via secrets:

```toml
GOOGLE_API_KEY = "your-key-here"
APP_MODE = "prod"
GEMINI_MODEL = "gemini-1.5-flash-latest"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_CONTEXT_CHARS = "5000"
```

---

## 🔧 Local Development

For local testing:
1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add your API key
3. Run: `streamlit run app.py`

The app automatically detects if it's running locally or in the cloud!

---

## ⚠️ Known Limitations (Free Tier)

- **No persistent storage**: ChromaDB resets on each deployment
- **Google Drive OAuth**: Won't work (requires local credentials)
- **File system**: Data folder is ephemeral

### Solutions:
- **For demo:** Pre-build your `chroma_db/` locally and commit it
- **For production:** Use cloud storage (S3, GCS) or paid Streamlit tier
- **Alternative:** Add file uploader in the UI for CV uploads

---

## 📱 Sharing Your App

Once deployed, Streamlit gives you a URL like:
```
https://pagie-app-[random-string].streamlit.app/
```

Share it with anyone - no login required! 🚀

---

## 🆘 Troubleshooting

**App crashes on startup?**
- Check secrets are added correctly
- Verify API key is valid
- Check Streamlit logs in the deployment dashboard

**Models loading slowly?**
- First run always takes 30-60 seconds (downloading models)
- Subsequent runs are cached and fast

**ChromaDB empty?**
- Cloud deployment starts fresh each time
- Solution: Commit your local `chroma_db/` folder (remove from .gitignore)

---

## 📚 Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [Streamlit Community Cloud](https://streamlit.io/cloud)
- [Manage Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
