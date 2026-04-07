"""
cloud_sync.py — Cloud-Aware CV File Sync for PAGie
==================================================
This module provides intelligent CV file synchronization that works both
locally (Google Drive OAuth) and on Streamlit Cloud (GCS bucket or repository).

Architecture:
  - Local: Uses sync_data.py (Google Drive OAuth)
  - Cloud: Uses GCS bucket download OR falls back to repository files
  
Usage:
  from cloud_sync import sync_cv_files
  
  sync_cv_files()  # Automatically detects environment
"""

import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CV_DATA_DIR = Path("./data/drive")
CV_DATA_DIR.mkdir(parents=True, exist_ok=True)

def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud."""
    try:
        import streamlit as st
        return hasattr(st, 'secrets')
    except ImportError:
        return False

def sync_cv_files() -> dict:
    """
    Sync CV files intelligently based on environment.
    
    Returns:
        dict: Status information with 'success', 'message', and 'file_count' keys.
    """
    
    if is_streamlit_cloud():
        return _sync_cloud()
    else:
        return _sync_local()

def _sync_local() -> dict:
    """Sync CV files locally using Google Drive OAuth."""
    try:
        from sync_data import run_sync
        
        logger.info("Running local Google Drive sync...")
        run_sync()
        
        # Count synced files
        file_count = len(list(CV_DATA_DIR.glob("*.pdf")))
        
        return {
            "success": True,
            "message": f"✅ Synced {file_count} CV files from Google Drive",
            "file_count": file_count
        }
        
    except Exception as e:
        logger.error(f"Local sync failed: {e}")
        return {
            "success": False,
            "message": f"❌ Sync failed: {str(e)}",
            "file_count": 0
        }

def _sync_cloud() -> dict:
    """
    Sync CV files on Streamlit Cloud.
    
    Strategy:
    1. Try Google Drive Sync (if GOOGLE_DRIVE_TOKEN_JSON configured in secrets)
    2. Try GCS bucket download (if configured)
    3. Fall back to using pre-committed files in repository
    """
    
    try:
        import streamlit as st
        # 1. Try Google Drive sync first if credentials are provided
        if "GOOGLE_DRIVE_TOKEN_JSON" in getattr(st, 'secrets', {}):
            logger.info("Token found in secrets, attempting direct Google Drive sync...")
            return _sync_local()
    except Exception as e:
        logger.error(f"Google Drive sync on cloud failed: {e}")
        pass
        
    # Try GCS sync if enabled
    try:
        import streamlit as st
        gcs_enabled = st.secrets.get("GCS_CV_SYNC_ENABLED", "false").lower() == "true"
        
        if gcs_enabled:
            return _sync_from_gcs()
    except (ImportError, AttributeError, KeyError):
        pass
    
    # No files available
    return {
        "success": False,
        "message": (
            "⚠️ No CV files available.\n\n"
            "**To use PAGie on Streamlit Cloud:**\n"
            "1. Pre-commit CV files to `data/drive/` in your repository\n"
            "2. OR configure GCS bucket sync in Streamlit secrets\n\n"
            "**For local development:**\n"
            "Run `python sync_data.py` with Google Drive OAuth setup."
        ),
        "file_count": 0
    }

def _sync_from_gcs() -> dict:
    """Download CV files from GCS bucket (optional advanced feature)."""
    try:
        import streamlit as st
        from google.cloud import storage
        import json
        
        bucket_name = st.secrets.get("GCS_BUCKET_NAME", "")
        credentials_json = st.secrets.get("GCS_CREDENTIALS_JSON", "")
        cv_prefix = st.secrets.get("GCS_CV_PREFIX", "pagie_cv_files/")
        
        if not bucket_name or not credentials_json:
            raise ValueError("GCS not properly configured")
        
        # Initialize GCS client
        credentials_dict = json.loads(credentials_json)
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        client = storage.Client(credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        # Download all PDF files from the CV prefix
        blobs = list(bucket.list_blobs(prefix=cv_prefix))
        pdf_blobs = [b for b in blobs if b.name.endswith('.pdf')]
        
        downloaded = 0
        for blob in pdf_blobs:
            filename = Path(blob.name).name
            local_path = CV_DATA_DIR / filename
            
            blob.download_to_filename(str(local_path))
            logger.info(f"Downloaded {filename} from GCS")
            downloaded += 1
        
        return {
            "success": True,
            "message": f"✅ Downloaded {downloaded} CV files from GCS bucket",
            "file_count": downloaded
        }
        
    except Exception as e:
        logger.error(f"GCS sync failed: {e}")
        
        # Fall back to repository files if any
        existing_files = list(CV_DATA_DIR.glob("*.pdf"))
        if existing_files:
            return {
                "success": True,
                "message": f"⚠️ GCS sync failed, using {len(existing_files)} repository files",
                "file_count": len(existing_files)
            }
        
        return {
            "success": False,
            "message": f"❌ GCS sync failed: {str(e)}",
            "file_count": 0
        }

def get_cv_file_status() -> dict:
    """
    Get current status of CV files.
    
    Returns:
        dict: Information about available CV files.
    """
    files = list(CV_DATA_DIR.glob("*.pdf"))
    
    return {
        "file_count": len(files),
        "files": [f.name for f in files],
        "total_size_mb": sum(f.stat().st_size for f in files) / (1024 * 1024) if files else 0,
        "location": str(CV_DATA_DIR),
        "environment": "Streamlit Cloud" if is_streamlit_cloud() else "Local Development"
    }
