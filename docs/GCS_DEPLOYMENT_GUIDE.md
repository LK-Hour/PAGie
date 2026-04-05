# 🚀 PAGie GCS Deployment Guide

Complete guide for deploying PAGie on Streamlit Cloud with Google Cloud Storage (GCS) for persistent ChromaDB storage.

---

## 📋 Prerequisites

- Google Cloud Platform (GCP) account ([Free Trial](https://cloud.google.com/free))
- Streamlit Cloud account ([Sign up free](https://streamlit.io/cloud))
- Your PAGie project pushed to GitHub

---

## Part 1: Google Cloud Storage Setup

### Step 1: Create a GCS Bucket

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Storage** → **Cloud Storage** → **Buckets**
3. Click **CREATE BUCKET**
4. Configure:
   - **Name**: `pagie-chromadb-storage` (must be globally unique)
   - **Location type**: Region (choose closest to you)
   - **Storage class**: Standard
   - **Access control**: Uniform
   - **Data protection**: None (for free tier)
5. Click **CREATE**

### Step 2: Create a Service Account

1. In Google Cloud Console, go to **IAM & Admin** → **Service Accounts**
2. Click **CREATE SERVICE ACCOUNT**
3. Configure:
   - **Name**: `pagie-storage-sync`
   - **Description**: "Service account for PAGie ChromaDB sync"
4. Click **CREATE AND CONTINUE**
5. Grant role: **Storage Object Admin**
6. Click **CONTINUE** → **DONE**

### Step 3: Generate JSON Key

1. Find your new service account in the list
2. Click the **three dots** (⋮) → **Manage keys**
3. Click **ADD KEY** → **Create new key**
4. Select **JSON** format
5. Click **CREATE**
6. **Save the downloaded JSON file** (you'll need it later)

### Step 4: Set Bucket Permissions (Optional)

If you encounter permission errors:
1. Go to your bucket → **Permissions** tab
2. Click **GRANT ACCESS**
3. Add your service account email (e.g., `pagie-storage-sync@your-project.iam.gserviceaccount.com`)
4. Role: **Storage Object Admin**
5. Click **SAVE**

---

## Part 2: Streamlit Cloud Deployment

### Step 1: Push Code to GitHub

```bash
# Ensure all GCS integration files are committed
git add gcs_sync.py app.py sync_data.py requirements.txt .streamlit/secrets.toml.example
git commit -m "Add GCS integration for cloud deployment"
git push origin main
```

### Step 2: Configure Streamlit Secrets

1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Deploy your app (or go to existing app settings)
3. Click **Settings** → **Secrets**
4. Paste the following (replace with your actual values):

```toml
# Google Gemini API Key
GOOGLE_API_KEY = "your-actual-gemini-api-key"

# Google Drive Folder ID
GOOGLE_DRIVE_FOLDER_ID = "your-drive-folder-id"

# GCS Configuration
GCS_ENABLED = "true"
GCS_BUCKET_NAME = "pagie-chromadb-storage"

# Service Account JSON (paste entire JSON as single-line string)
GCS_CREDENTIALS_JSON = """{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"pagie-storage-sync@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}"""
```

**Important**: When pasting the JSON:
- Remove all line breaks (make it a single line)
- Wrap it in triple quotes `"""`
- Escape existing quotes if needed

### Step 3: Deploy the App

1. In Streamlit Cloud, click **Deploy**
2. Select your GitHub repository
3. Main file: `app.py`
4. Click **Deploy**
5. Wait for deployment (3-5 minutes)

### Step 4: Verify GCS Sync

Check the app logs for:
```
INFO - GCS client initialized with service account credentials
INFO - ChromaDB not found locally - syncing from cloud...
INFO - ChromaDB sync complete: X downloaded, Y skipped
```

---

## Part 3: Local Development with GCS

### Option 1: Using Service Account Key File

1. Save your service account JSON key to a secure location:
   ```bash
   mkdir -p ~/.gcp
   mv ~/Downloads/pagie-storage-sync-*.json ~/.gcp/pagie-sa-key.json
   chmod 600 ~/.gcp/pagie-sa-key.json
   ```

2. Update your `.env` file:
   ```bash
   GCS_ENABLED=true
   GCS_BUCKET_NAME=pagie-chromadb-storage
   GCS_CREDENTIALS_JSON=/home/your-username/.gcp/pagie-sa-key.json
   ```

3. Test the sync:
   ```bash
   python gcs_sync.py --download
   python gcs_sync.py --upload
   ```

### Option 2: Using Application Default Credentials (ADC)

1. Install Google Cloud SDK:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install google-cloud-sdk
   
   # macOS
   brew install google-cloud-sdk
   ```

2. Authenticate:
   ```bash
   gcloud auth application-default login
   ```

3. Update `.env`:
   ```bash
   GCS_ENABLED=true
   GCS_BUCKET_NAME=pagie-chromadb-storage
   # Leave GCS_CREDENTIALS_JSON empty to use ADC
   GCS_CREDENTIALS_JSON=
   ```

---

## Part 4: Usage & Workflows

### Automatic Sync Workflow

The GCS sync happens automatically:

1. **App Startup** (on Streamlit Cloud):
   - `app.py` calls `ensure_chromadb_synced()`
   - Downloads ChromaDB from GCS if not present locally

2. **After Data Update**:
   - `sync_data.py` finishes downloading CV files
   - Calls `auto_sync_after_update()`
   - Uploads updated ChromaDB to GCS

### Manual Sync Commands

```bash
# Download ChromaDB from cloud
python gcs_sync.py --download

# Upload ChromaDB to cloud
python gcs_sync.py --upload

# Force full sync (no incremental)
python gcs_sync.py --upload --force
python gcs_sync.py --download --force
```

### Incremental Sync

The GCS sync is intelligent:
- **Download**: Only downloads files that don't exist locally
- **Upload**: Only uploads files that have changed (based on MD5 hash)
- Saves bandwidth and speeds up deployments

---

## Part 5: Cost Management (Free Tier)

### GCS Free Tier Limits (as of 2024)

- **5 GB** storage per month
- **5,000** Class A operations (uploads)
- **50,000** Class B operations (downloads)
- **1 GB** network egress to worldwide destinations

### Monitoring Usage

1. Go to Google Cloud Console → **Billing**
2. Click **Reports** → Filter by **Cloud Storage**
3. Check your usage against free tier limits

### Estimated PAGie Usage

Assuming a typical ChromaDB size of **100-500 MB**:
- **Storage**: ~500 MB (well under 5 GB limit)
- **Daily syncs**: ~2 uploads/day = 60/month (well under 5,000 limit)
- **App restarts**: ~10 downloads/day = 300/month (well under 50,000 limit)

**Result**: Should stay within free tier indefinitely! 🎉

---

## Part 6: Troubleshooting

### Issue 1: "GCS client not available"

**Symptom**: App logs show "GCS client not available - cannot sync"

**Solutions**:
1. Check if `google-cloud-storage` is in `requirements.txt`
2. Verify Streamlit secrets are correctly set
3. Ensure service account JSON is valid (test with `json.loads()`)

### Issue 2: "Permission denied" when accessing bucket

**Solutions**:
1. Verify service account has **Storage Object Admin** role
2. Check bucket permissions (add service account explicitly)
3. Ensure bucket name matches exactly

### Issue 3: ChromaDB not persisting between deploys

**Solutions**:
1. Check `GCS_ENABLED = "true"` in Streamlit secrets
2. Verify logs show "ChromaDB sync complete"
3. Check GCS bucket in console for uploaded files

### Issue 4: "Module not found: google.cloud"

**Solution**: Add to `requirements.txt`:
```
google-cloud-storage
```

### Issue 5: Slow app startup

**Cause**: Large ChromaDB download on first run

**Solutions**:
1. Use incremental sync (default behavior)
2. Pre-upload ChromaDB to GCS before first deploy
3. Consider reducing vector database size with better chunking

---

## Part 7: Best Practices

### Security

✅ **DO**:
- Store service account keys in Streamlit secrets (never in code)
- Use `.gitignore` to exclude `secrets.toml` and `.env`
- Restrict service account to minimum required permissions
- Rotate service account keys regularly (every 90 days)

❌ **DON'T**:
- Commit service account JSON to Git
- Share service account keys publicly
- Grant overly broad IAM roles

### Performance

- Use **incremental sync** (default) to minimize bandwidth
- Upload ChromaDB only after significant data changes
- Monitor GCS operations to stay within free tier

### Backup

Consider manual backups:
```bash
# Download ChromaDB from GCS
gsutil -m cp -r gs://pagie-chromadb-storage/pagie_chromadb/ ./backup/

# Upload backup to GCS
gsutil -m cp -r ./backup/ gs://pagie-chromadb-storage/backup_$(date +%Y%m%d)/
```

---

## Part 8: Alternative Free Storage Options

If you prefer not to use GCS:

### Option 1: GitHub Repository Storage
- Store `chroma_db/` in your repo
- ⚠️ Limited to 1 GB repo size
- ⚠️ Not recommended for frequently updated data

### Option 2: Supabase Storage
- 1 GB free storage
- Easy to integrate with Python
- Good for smaller databases

### Option 3: Cloudflare R2
- 10 GB free storage
- S3-compatible API
- No egress fees

---

## 🎓 Summary

You've successfully integrated GCS for persistent ChromaDB storage! Your PAGie app will now:

✅ Download ChromaDB from GCS on startup  
✅ Upload changes after data syncs  
✅ Persist knowledge base across Streamlit Cloud restarts  
✅ Stay within GCS free tier limits  
✅ Work seamlessly in both local and cloud environments  

**Next Steps**:
1. Test the deployment on Streamlit Cloud
2. Monitor GCS usage in Google Cloud Console
3. Enjoy your persistent RAG-powered CV analysis system! 🚀

---

## 📚 Additional Resources

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Streamlit Cloud Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [GCS Free Tier Details](https://cloud.google.com/free)

---

**Questions or Issues?** Open an issue on GitHub or contact the PAGie team.
