# ChromaDB on Streamlit Cloud

## Understanding the Issue

Streamlit Cloud has a **read-only filesystem** except for `/tmp`. ChromaDB needs to write data, so we use `/tmp/chroma_db`.

## ⚠️ Important: /tmp is Ephemeral

The `/tmp` directory is **temporary** and gets wiped when:
- The app restarts
- Streamlit Cloud restarts the container
- After periods of inactivity

**This means ChromaDB will be rebuilt on each restart.**

## How PAGie Handles This

### ✅ Option 1: Auto-Rebuild (Current Setup - No Config Needed)

**What happens:**
1. App starts → ChromaDB not found in `/tmp`
2. User clicks "Rebuild KB" button
3. ChromaDB builds from CV files in `data/drive/`
4. Works until next restart

**Pros:**
- ✅ No configuration needed
- ✅ Works immediately on deployment
- ✅ Always uses latest CV files

**Cons:**
- ⚠️ Rebuilds on every restart (1-2 minutes)
- ⚠️ Need to click "Rebuild KB" after deployment

### 🚀 Option 2: GCS Persistence (Advanced - Optional)

**What happens:**
1. App starts → Downloads ChromaDB from GCS bucket
2. User clicks "Rebuild KB" → Auto-uploads to GCS
3. Next restart → Downloads existing ChromaDB (instant!)

**Setup:**

1. **Create GCS Bucket:**
   ```bash
   gsutil mb gs://pagie-chromadb-backup
   ```

2. **Create Service Account:**
   - Go to Google Cloud Console → IAM
   - Create service account with "Storage Object Admin" role
   - Download JSON key

3. **Add to Streamlit Secrets:**
   ```toml
   # Enable GCS sync
   GCS_ENABLED = "true"
   GCS_BUCKET_NAME = "pagie-chromadb-backup"
   
   # Paste service account JSON (one line, no newlines)
   GCS_CREDENTIALS_JSON = '{"type":"service_account","project_id":"..."}'
   ```

4. **Deploy:** ChromaDB persists across restarts!

## Comparison

| Feature | Auto-Rebuild | GCS Persistence |
|---------|--------------|-----------------|
| Setup | None needed | GCS bucket + secrets |
| Restart time | 1-2 min rebuild | Instant (downloads) |
| Cost | Free | ~$0.026/GB/month |
| Best for | Testing, demos | Production |

## Current Status

✅ **PAGie works with auto-rebuild** (Option 1)
- CV files are in repository
- Click "Rebuild KB" when app starts
- No configuration needed

💡 **Upgrade to GCS** when you need:
- Faster cold starts
- Production deployment
- Persistent ChromaDB

## Testing the Fix

1. **Click "Rebuild KB"**
   - Should complete without readonly error
   - ChromaDB builds in `/tmp/chroma_db/`

2. **Ask a question**
   - ChromaDB should return relevant CV context

3. **Restart app** (simulate)
   - ChromaDB gone from /tmp
   - Click "Rebuild KB" again
   - Works as expected

## Files Modified

- `rag_pipeline.py`: Auto-detects cloud, uses `/tmp/chroma_db`
- `gcs_sync.py`: Syncs ChromaDB to/from GCS bucket
- `data_science_eda.py`: Builds ChromaDB in writable location
- `ui/components/sidebar.py`: Auto-syncs to GCS after rebuild
