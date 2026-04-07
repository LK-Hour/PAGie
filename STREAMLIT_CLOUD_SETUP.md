# 🚀 Streamlit Cloud Setup Instructions

## ⚙️ Configure Secrets in Streamlit Cloud

Your CV files are already committed to the repository (`data/drive/` contains 3 PDFs). Now you need to configure the Streamlit Cloud secrets:

### Steps:

1. **Go to Streamlit Cloud Dashboard:**
   - https://share.streamlit.io/
   - Navigate to your PAGie app

2. **Open Settings → Secrets:**
   - Click on your app
   - Go to "Settings" (⚙️ icon)
   - Click "Secrets" tab

3. **Copy and Paste This Configuration:**

```toml
# --- Application Mode ---
# Set to "prod" for Streamlit Cloud (uses Gemini)
APP_MODE = "prod"

# --- Gemini Model ---
# Use gemini-2.5-flash for latest performance
GEMINI_MODEL = "gemini-2.5-flash"

# --- Google Gemini API Key ---
GOOGLE_API_KEY = "AIzaSyAdHMc2Ta1SOnmEwsmgwJ7r1epgQRSKM9k"

# --- Google Drive Folder ID (optional - CVs are pre-committed) ---
GOOGLE_DRIVE_FOLDER_ID = "1mPmXrJbqbaxFkbpEbUKJlfYjUgbFKCpW"

# --- Google Cloud Storage Configuration (optional - not using yet) ---
GCS_ENABLED = "false"
```

4. **Click "Save"**

5. **Wait for automatic reboot** (~30 seconds)

---

## ✅ What This Does:

### APP_MODE = "prod"
- ✅ Uses Google Gemini 3.0 Flash (not local Ollama)
- ✅ Production-ready LLM responses
- ✅ Faster and more accurate answers

### CV Files Location:
The app will look for CV files in this order:
1. ✅ **Pre-committed files** in `data/drive/` (already in repo) ← **USING THIS**
2. Google Drive sync (if configured)
3. GCS bucket (if configured)

Since CV files are already committed, **no additional sync is needed!**

---

## 🐛 Current Issues Fixed:

### Issue 1: "No CV files available"
**Solution:** CV files ARE in the repo at `data/drive/`, but the sync script might be looking in the wrong place on Streamlit Cloud.

### Issue 2: "dev mode instead of prod mode"
**Solution:** Add `APP_MODE = "prod"` to Streamlit secrets.

---

## 🔍 Verify Setup:

After saving secrets and reboot:
1. Check the sidebar - should say **"🚀 Mode: Production (Gemini)"**
2. Check CV files - should show **"3 CVs loaded"**
3. Try a query - should get Gemini-powered answer

---

## 📝 Notes:

- **API Key Security:** The key in secrets is only visible to you and your app
- **CV Files:** Already committed (560 KB total - safe for Git)
- **ChromaDB:** Will be synced from `data/chromadb_prebuilt/` on first run
- **GCS:** Not needed yet since everything is in Git

---

Good luck! 🎓✨
