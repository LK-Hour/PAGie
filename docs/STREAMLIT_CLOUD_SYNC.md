# CV File Sync on Streamlit Cloud

## Current Setup (Repository Files)

✅ **Already Working!** The app now includes 3 CV files in the repository:
- `data/drive/KIMHOUR_LOEM_CV.pdf`
- `data/drive/Luy_Virak_CV.pdf`
- `data/drive/LY_KIMKHENG_CV.pdf`

When you click "Sync Files" on Streamlit Cloud, it will use these pre-committed files automatically.

## How to Update CV Files

### Option 1: Commit New Files to Repository (Recommended)

1. **Locally:** Add new CV files to `data/drive/`
   ```bash
   cp path/to/new_cv.pdf data/drive/
   ```

2. **Commit and push:**
   ```bash
   git add data/drive/*.pdf
   git commit -m "Update CV files"
   git push
   ```

3. **Rebuild on Streamlit Cloud:** Click "Rebuild KB" button

### Option 2: Google Cloud Storage Sync (Advanced)

For dynamic file updates without redeploying, you can configure GCS bucket sync:

1. **Create GCS Bucket:**
   - Go to Google Cloud Console
   - Create a bucket (e.g., `pagie-cv-files`)
   - Upload CV files to folder: `pagie_cv_files/`

2. **Create Service Account:**
   - Create service account with Storage Object Viewer permission
   - Download JSON key file

3. **Add to Streamlit Secrets:**
   
   In Streamlit Cloud dashboard, add to secrets:
   ```toml
   # Google Cloud Storage Configuration
   GCS_CV_SYNC_ENABLED = "true"
   GCS_BUCKET_NAME = "your-bucket-name"
   GCS_CV_PREFIX = "pagie_cv_files/"
   
   # Paste entire JSON key (one line, no newlines)
   GCS_CREDENTIALS_JSON = '{"type":"service_account","project_id":"your-project",...}'
   ```

4. **Update CV Files:**
   - Upload new files to GCS bucket
   - Click "Sync Files" in app
   - Files download from GCS automatically

## Local Development

On your local machine, the sync button works differently:

```bash
# Set up Google Drive OAuth (one-time)
python sync_data.py

# Or click "Sync Files" in the app
# Opens browser for Google OAuth authentication
```

## Architecture

```
┌─────────────────┐
│ Environment?    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐   ┌─▼────────┐
│Local │   │ Cloud    │
└───┬──┘   └─┬────────┘
    │        │
┌───▼──────┐ │
│Google    │ │
│Drive     │ │
│OAuth     │ │
└──────────┘ │
             │
        ┌────┴─────┐
        │          │
    ┌───▼───┐  ┌──▼──────┐
    │Repo   │  │GCS      │
    │Files  │  │Bucket   │
    │(Default)│ │(Optional)│
    └───────┘  └─────────┘
```

## Benefits

✅ **No OAuth needed on cloud** - Uses repository or GCS  
✅ **Fast deployment** - Files already in repository  
✅ **Version controlled** - CV files tracked in git  
✅ **Optional GCS** - For dynamic updates without redeployment  
