"""
gcs_sync.py — Google Cloud Storage Sync for PAGie ChromaDB
===========================================================
This module handles syncing the ChromaDB vector database to/from Google Cloud Storage
for persistent storage when deploying PAGie on Streamlit Cloud.

Features:
  - Automatic sync on app startup (download ChromaDB from GCS)
  - Automatic sync after data updates (upload ChromaDB to GCS)
  - Incremental sync to minimize bandwidth usage
  - Error handling with retry logic
  - Support for both local development and cloud deployment

Architecture:
  GCS Bucket → Download to ./chroma_db/ → RAG Pipeline → Upload changes → GCS Bucket

Usage:
  from gcs_sync import sync_chromadb_from_cloud, sync_chromadb_to_cloud
  
  # At app startup
  sync_chromadb_from_cloud()
  
  # After updating ChromaDB
  sync_chromadb_to_cloud()
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, List

# Environment management - optional for Streamlit Cloud
try:
    from dotenv import load_dotenv
    _dotenv_available = True
except ImportError:
    # On Streamlit Cloud, dotenv is not needed (uses st.secrets instead)
    _dotenv_available = False

from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables (only if dotenv is available)
if _dotenv_available:
    load_dotenv()

# Support both Streamlit secrets (cloud) and .env (local)
try:
    import streamlit as st
    GCS_ENABLED = st.secrets.get("GCS_ENABLED", os.getenv("GCS_ENABLED", "false")).lower() == "true"
    GCS_BUCKET_NAME = st.secrets.get("GCS_BUCKET_NAME", os.getenv("GCS_BUCKET_NAME", ""))
    GCS_CREDENTIALS_JSON = st.secrets.get("GCS_CREDENTIALS_JSON", os.getenv("GCS_CREDENTIALS_JSON", ""))
except (ImportError, FileNotFoundError, AttributeError):
    GCS_ENABLED = os.getenv("GCS_ENABLED", "false").lower() == "true"
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
    GCS_CREDENTIALS_JSON = os.getenv("GCS_CREDENTIALS_JSON", "")

# Configuration
# Use writable directory on Streamlit Cloud
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        CHROMA_DB_PATH = Path("/tmp/chroma_db")
    else:
        CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "./chroma_db"))
except (ImportError, AttributeError):
    CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "./chroma_db"))

GCS_CHROMA_PREFIX = "pagie_chromadb/"  # Folder in GCS bucket
MANIFEST_FILE = CHROMA_DB_PATH / ".gcs_manifest.json"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Cloud Storage Client Initialization
# ---------------------------------------------------------------------------

_gcs_client = None

def _get_gcs_client():
    """
    Get or create Google Cloud Storage client.
    Supports both service account JSON and Application Default Credentials.
    """
    global _gcs_client
    
    if not GCS_ENABLED:
        logger.info("GCS sync is disabled (GCS_ENABLED=false)")
        return None
    
    if _gcs_client is not None:
        return _gcs_client
    
    try:
        from google.cloud import storage
        from google.oauth2 import service_account
        
        # Try service account credentials first (for Streamlit Cloud)
        if GCS_CREDENTIALS_JSON:
            # Parse JSON credentials
            if GCS_CREDENTIALS_JSON.startswith("{"):
                credentials_dict = json.loads(GCS_CREDENTIALS_JSON)
            else:
                # Assume it's a file path
                with open(GCS_CREDENTIALS_JSON, 'r') as f:
                    credentials_dict = json.load(f)
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )
            _gcs_client = storage.Client(credentials=credentials)
            logger.info("GCS client initialized with service account credentials")
        else:
            # Use Application Default Credentials (for local development)
            _gcs_client = storage.Client()
            logger.info("GCS client initialized with Application Default Credentials")
        
        return _gcs_client
    
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        return None

# ---------------------------------------------------------------------------
# File Hashing for Incremental Sync
# ---------------------------------------------------------------------------

def _hash_file(file_path: Path) -> str:
    """Calculate MD5 hash of a file for change detection."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def _load_manifest() -> Dict[str, str]:
    """Load the local sync manifest (file_path -> hash)."""
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}")
    return {}

def _save_manifest(manifest: Dict[str, str]):
    """Save the local sync manifest."""
    try:
        MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")

# ---------------------------------------------------------------------------
# Download ChromaDB from GCS
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def sync_chromadb_from_cloud(force: bool = False) -> bool:
    """
    Download ChromaDB from Google Cloud Storage to local disk.
    
    Args:
        force: If True, re-download all files regardless of local state
        
    Returns:
        True if sync was successful, False otherwise
    """
    if not GCS_ENABLED:
        logger.info("GCS sync disabled - skipping download")
        return True
    
    client = _get_gcs_client()
    if not client:
        logger.error("GCS client not available - cannot sync from cloud")
        return False
    
    if not GCS_BUCKET_NAME:
        logger.error("GCS_BUCKET_NAME not set - cannot sync from cloud")
        return False
    
    try:
        from google.cloud import storage
        
        logger.info(f"Starting ChromaDB sync from GCS bucket: {GCS_BUCKET_NAME}")
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # List all blobs in the ChromaDB folder
        blobs = list(bucket.list_blobs(prefix=GCS_CHROMA_PREFIX))
        
        if not blobs:
            logger.warning(f"No ChromaDB files found in GCS at {GCS_CHROMA_PREFIX}")
            return True
        
        # Create temp directory for download
        CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
        
        downloaded_count = 0
        skipped_count = 0
        
        for blob in blobs:
            # Skip directory markers
            if blob.name.endswith('/'):
                continue
            
            # Calculate local path
            relative_path = blob.name[len(GCS_CHROMA_PREFIX):]
            local_path = CHROMA_DB_PATH / relative_path
            
            # Create parent directories
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            if force or not local_path.exists():
                logger.info(f"Downloading: {blob.name} → {local_path}")
                blob.download_to_filename(str(local_path))
                downloaded_count += 1
            else:
                skipped_count += 1
        
        logger.info(f"ChromaDB sync complete: {downloaded_count} downloaded, {skipped_count} skipped")
        return True
    
    except Exception as e:
        logger.error(f"Failed to sync ChromaDB from cloud: {e}")
        return False

# ---------------------------------------------------------------------------
# Upload ChromaDB to GCS
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def sync_chromadb_to_cloud(incremental: bool = True) -> bool:
    """
    Upload ChromaDB from local disk to Google Cloud Storage.
    
    Args:
        incremental: If True, only upload changed files (faster)
        
    Returns:
        True if sync was successful, False otherwise
    """
    if not GCS_ENABLED:
        logger.info("GCS sync disabled - skipping upload")
        return True
    
    client = _get_gcs_client()
    if not client:
        logger.error("GCS client not available - cannot sync to cloud")
        return False
    
    if not GCS_BUCKET_NAME:
        logger.error("GCS_BUCKET_NAME not set - cannot sync to cloud")
        return False
    
    if not CHROMA_DB_PATH.exists():
        logger.warning(f"ChromaDB path does not exist: {CHROMA_DB_PATH}")
        return True
    
    try:
        from google.cloud import storage
        
        logger.info(f"Starting ChromaDB sync to GCS bucket: {GCS_BUCKET_NAME}")
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Load manifest for incremental sync
        manifest = _load_manifest() if incremental else {}
        new_manifest = {}
        
        uploaded_count = 0
        skipped_count = 0
        
        # Walk through ChromaDB directory
        for file_path in CHROMA_DB_PATH.rglob('*'):
            if file_path.is_file() and file_path.name != '.gcs_manifest.json':
                # Calculate relative path for GCS
                relative_path = file_path.relative_to(CHROMA_DB_PATH)
                blob_name = f"{GCS_CHROMA_PREFIX}{relative_path.as_posix()}"
                
                # Calculate file hash for change detection
                file_hash = _hash_file(file_path)
                new_manifest[str(relative_path)] = file_hash
                
                # Check if file has changed
                if incremental and manifest.get(str(relative_path)) == file_hash:
                    skipped_count += 1
                    continue
                
                # Upload file
                logger.info(f"Uploading: {file_path} → {blob_name}")
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(str(file_path))
                uploaded_count += 1
        
        # Save new manifest
        _save_manifest(new_manifest)
        
        logger.info(f"ChromaDB sync complete: {uploaded_count} uploaded, {skipped_count} skipped")
        return True
    
    except Exception as e:
        logger.error(f"Failed to sync ChromaDB to cloud: {e}")
        return False

# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def ensure_chromadb_synced():
    """
    Ensure ChromaDB is synced from cloud on first run.
    Call this at app startup before initializing RAG pipeline.
    """
    if GCS_ENABLED and not CHROMA_DB_PATH.exists():
        logger.info("ChromaDB not found locally - syncing from cloud...")
        sync_chromadb_from_cloud()

def auto_sync_after_update():
    """
    Automatically sync ChromaDB to cloud after data updates.
    Call this after sync_data.py completes or after manual data ingestion.
    """
    if GCS_ENABLED:
        logger.info("Data updated - syncing ChromaDB to cloud...")
        sync_chromadb_to_cloud(incremental=True)

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync ChromaDB with Google Cloud Storage")
    parser.add_argument("--download", action="store_true", help="Download ChromaDB from GCS")
    parser.add_argument("--upload", action="store_true", help="Upload ChromaDB to GCS")
    parser.add_argument("--force", action="store_true", help="Force full sync (no incremental)")
    
    args = parser.parse_args()
    
    if args.download:
        success = sync_chromadb_from_cloud(force=args.force)
        print(f"Download {'successful' if success else 'failed'}")
    elif args.upload:
        success = sync_chromadb_to_cloud(incremental=not args.force)
        print(f"Upload {'successful' if success else 'failed'}")
    else:
        print("Please specify --download or --upload")
