# 🚨 URGENT: Streamlit Cloud Configuration

## ❌ Current Issues:
1. **0 Chunks** - ChromaDB not loading
2. **Wrong Model** - Still using gemini-2.0-flash-exp instead of gemini-2.5-flash

## ✅ Root Cause:
**You haven't added the secrets to Streamlit Cloud dashboard yet!**

Without secrets:
- APP_MODE defaults to "dev" (not "prod")
- GEMINI_MODEL defaults to "gemini-2.0-flash-exp"
- ChromaDB sync might fail due to environment detection

---

## 🔥 IMMEDIATE ACTION REQUIRED:

### Step 1: Open Streamlit Cloud Dashboard
1. Go to: https://share.streamlit.io/
2. Click on your **PAGie** app
3. Click **Settings** ⚙️ (top right)
4. Click **Secrets** tab

### Step 2: Paste This EXACTLY (Copy & Paste):
```toml
# Application Mode
APP_MODE = "prod"

# Gemini Model
GEMINI_MODEL = "gemini-2.5-flash"

# Google API Key
GOOGLE_API_KEY = "AIzaSyAdHMc2Ta1SOnmEwsmgwJ7r1epgQRSKM9k"

# Optional
GCS_ENABLED = "false"
```

### Step 3: Save
1. Click **"Save"** button at bottom
2. Wait 30 seconds for automatic reboot
3. Refresh your app

---

## 🧪 How to Verify It Works:

After adding secrets and rebooting, you should see:

### ✅ Expected Results:
- **Sidebar Status:**
  - Mode: `🚀 Production (Gemini)`
  - Model: `gemini-2.5-flash`
  - CV Files: `3 files found`
  - Chunks: `16 chunks loaded`

- **Query Test:**
  - Try: "What programming languages do candidates know?"
  - Should get detailed answer with sources

### ❌ If Still Shows 0 Chunks:
The issue might be with ChromaDB path on Streamlit Cloud. Check the logs for:
- "📦 Copying pre-built ChromaDB from..."
- "✅ Pre-built ChromaDB copied successfully!"

---

## 🔍 Debugging Steps:

If it still doesn't work after adding secrets:

1. **Check Streamlit Cloud Logs:**
   - In app dashboard, click "Manage app"
   - Look for errors in the logs
   - Search for "ChromaDB" or "chroma_db"

2. **Common Issues:**

   **Issue A: ChromaDB not found**
   ```
   ⚠️ ChromaDB not found locally
   ```
   **Solution:** Files are committed. Check if gcs_sync.py is running properly.

   **Issue B: Environment detection wrong**
   ```
   Environment: local
   ```
   **Solution:** Should say "cloud". Check environment variables.

   **Issue C: Model not found**
   ```
   Model gemini-2.5-flash not found
   ```
   **Solution:** Change GEMINI_MODEL to "gemini-2.0-flash-exp" in secrets.

---

## 📋 Quick Checklist:

- [ ] Opened Streamlit Cloud dashboard
- [ ] Clicked Settings → Secrets
- [ ] Pasted the exact TOML config above
- [ ] Clicked "Save"
- [ ] Waited 30 seconds for reboot
- [ ] Refreshed the app page
- [ ] Checked sidebar shows "Production" mode
- [ ] Checked sidebar shows "16 chunks"
- [ ] Tested a query

---

## 💡 Why This Matters:

**Without secrets in Streamlit Cloud:**
- Your app runs in "dev" mode (tries to use local Ollama which doesn't exist)
- Uses default model from code (gemini-2.0-flash-exp)
- Environment detection might fail
- ChromaDB sync might not work

**With secrets:**
- App runs in "prod" mode (uses Gemini API)
- Uses your specified model (gemini-2.5-flash)
- Proper environment detection
- ChromaDB syncs from repository

---

## 🆘 If Still Broken:

Share the **Streamlit Cloud logs** (first 50 lines after reboot) so I can see what's failing.

---

**DO THIS NOW! Your app will work after adding secrets! 🚀**
