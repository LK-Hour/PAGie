"""
sync_data_local.py — Local-Only ETL Pipeline for PAGie (CV-Focused)
====================================================================
Pure local version of the sync pipeline with NO cloud sync logic.
This version is optimized for local development with Google Drive OAuth only.

Key Features:
  - Google Drive OAuth sync (local token.json)
  - Local data storage (./data/drive)
  - Local sync state (./data/sync_state.json)
  - No GCS/cloud sync logic
  - Smart incremental sync

Usage:
  python sync_data_local.py          # Runs once immediately, then schedules nightly
"""

import glob
import io
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import schedule
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Load API keys and config from .env — never hardcode credentials.
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Google Drive OAuth scope (read-only — we never modify the user's Drive).
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Local token file — stores the OAuth token after first login so we don't
# have to re-authenticate on every run.
TOKEN_FILE = "token.json"

# Supported Google Drive MIME types — focused on CV/Resume formats.
SUPPORTED_MIME_TYPES = [
    "application/vnd.google-apps.document",       # Google Docs
    "application/pdf",                            # PDFs
    "text/plain",                                 # Plain text files
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
]

# REQUIRED: Specific Google Drive folder ID containing CV files
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()

if not GOOGLE_DRIVE_FOLDER_ID:
    raise ValueError(
        "GOOGLE_DRIVE_FOLDER_ID is required in .env file. "
        "PAGie is now focused on a specific folder containing CV files."
    )

# Local directories for storing raw downloaded CV data.
DATA_DIR = Path("./data")
DRIVE_DIR = DATA_DIR / "drive"

# Ensure directories exist before writing.
DATA_DIR.mkdir(exist_ok=True)
DRIVE_DIR.mkdir(exist_ok=True)

# Sync-state manifest — records the last-known modification timestamp
SYNC_STATE_FILE = DATA_DIR / "sync_state.json"

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ===========================================================================
# SYNC-STATE HELPERS — Incremental / Smart Sync
# ===========================================================================

def load_sync_state() -> dict:
    """
    Loads the persisted sync-state manifest from disk.

    The manifest is a JSON dict with "drive" key:
      - "drive": maps Drive file IDs → {"modified_time": str, "local_path": str, "file_name": str}

    Returns:
        The manifest dict, or an empty skeleton if no state file exists yet.
    """
    if SYNC_STATE_FILE.exists():
        try:
            with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read sync state ({e}). Starting fresh.")
    return {"drive": {}}


def save_sync_state(state: dict) -> None:
    """
    Persists the sync-state manifest to disk after every sync run.

    Args:
        state: The full manifest dict (drive section).
    """
    try:
        with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError as e:
        logger.error(f"Failed to save sync state: {e}")


# ===========================================================================
# GOOGLE DRIVE — Authentication & Download
# ===========================================================================

def get_google_drive_service():
    """
    Authenticates with the Google Drive API using OAuth 2.0 (local only).

    On first run, this opens a browser window for the user to grant permission.
    The resulting token is saved to token.json so subsequent runs are silent.

    Returns:
        A Google Drive API service object ready to make requests.

    Raises:
        FileNotFoundError: If no client_secret_*.json file exists in the project root.
    """
    creds = None

    # Try to load local token.json
    if os.path.exists(TOKEN_FILE):
        logger.info(f"Loading local credentials from {TOKEN_FILE}...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there's no valid token, initiate the OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Silently refresh an expired token using the stored refresh token.
            logger.info("Refreshing expired Google OAuth token...")
            creds.refresh(Request())
        else:
            # First-time auth — find the client secret file automatically.
            secret_files = glob.glob("client_secret_*.json")
            if not secret_files:
                raise FileNotFoundError(
                    "No client_secret_*.json found. Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(secret_files[0], SCOPES)
            # Opens a browser window for the user to log in and grant permission.
            creds = flow.run_local_server(port=0)

        # Persist the token so we don't need to re-authenticate next run
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        logger.info("Google OAuth token saved to token.json.")

    return build("drive", "v3", credentials=creds)


def _list_all_drive_files(service) -> list:
    """
    Retrieves every supported file from the specified Google Drive folder.

    Uses the Drive API's pagination (nextPageToken) to handle folders
    with more than 1000 files. Only files matching SUPPORTED_MIME_TYPES
    are returned.

    Args:
        service: An authenticated Google Drive API service object.

    Returns:
        A flat list of file metadata dicts: {id, name, mimeType, modifiedTime}.
    """
    # Build a MIME type filter
    mime_filter = " or ".join([f"mimeType='{m}'" for m in SUPPORTED_MIME_TYPES])

    # Restrict traversal to the specific CV folder.
    query = (
        f"trashed=false and ({mime_filter}) and "
        f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents"
    )
    logger.info(f"Drive sync scoped to CV folder ID: {GOOGLE_DRIVE_FOLDER_ID}")

    all_files = []
    page_token = None

    while True:
        kwargs = {
            "q": query,
            "fields": "nextPageToken, files(id, name, mimeType, modifiedTime)",
            "pageSize": 1000,
            "orderBy": "name",
        }
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.files().list(**kwargs).execute()
        all_files.extend(results.get("files", []))

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return all_files


def download_drive_files():
    """
    Smart-syncs supported files from the specified Google Drive folder.

    Uses the local sync-state manifest (data/sync_state.json) to record each
    file's modifiedTime. On each run:
      - **New files** (not in the manifest) are downloaded.
      - **Modified files** (remote modifiedTime != cached value) are re-downloaded.
      - **Unchanged files** (same modifiedTime + local file exists) are skipped.
      - **Deleted files** (in manifest but no longer on Drive) are removed.

    Supported file types:
      - Google Docs        → exported as plain text (.txt)
      - PDFs               → downloaded directly (.pdf)
      - Plain text files   → downloaded directly (.txt)
      - DOCX files        → downloaded directly (.docx)
    """
    try:
        service = get_google_drive_service()

        # Retrieve every supported file from the folder
        files = _list_all_drive_files(service)
        logger.info(f"Found {len(files)} supported file(s) in Google Drive folder.")

        # Load the persisted sync state to compare timestamps.
        state = load_sync_state()
        drive_state = state.get("drive", {})

        # Build a set of current remote file IDs to detect deleted files.
        remote_ids = {f["id"] for f in files}

        # --- Cleanup: remove local files that no longer exist on Drive ---
        stale_ids = [fid for fid in list(drive_state.keys()) if fid not in remote_ids]
        for fid in stale_ids:
            entry = drive_state.pop(fid)
            stale_path = Path(entry.get("local_path", ""))
            if stale_path.exists():
                stale_path.unlink()
                logger.info(f"  🗑️  Removed stale file: {stale_path.name}")

        downloaded = 0
        skipped = 0
        errors = 0

        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            mime_type = file["mimeType"]
            remote_modified = file.get("modifiedTime", "")

            # Determine the local save path based on MIME type.
            if mime_type in (
                "application/vnd.google-apps.document",
                "application/vnd.google-apps.presentation",
            ):
                save_path = DRIVE_DIR / f"{file_name}.txt"
            else:
                save_path = DRIVE_DIR / file_name

            # --- Smart-skip: only download if the file changed or is missing locally ---
            cached = drive_state.get(file_id, {})
            if cached.get("modified_time") == remote_modified and save_path.exists():
                logger.debug(f"  ⏭️  Unchanged, skipping: {file_name}")
                skipped += 1
                continue

            try:
                # Google Workspace files have no binary form — they must be exported.
                if mime_type in (
                    "application/vnd.google-apps.document",
                    "application/vnd.google-apps.presentation",
                ):
                    request = service.files().export_media(
                        fileId=file_id, mimeType="text/plain"
                    )
                else:
                    # PDFs and plain text files are downloaded as-is.
                    request = service.files().get_media(fileId=file_id)

                # Stream the file to disk in memory-efficient chunks.
                with io.FileIO(str(save_path), "wb") as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()

                # Record the new timestamp and local path in the manifest.
                drive_state[file_id] = {
                    "modified_time": remote_modified,
                    "local_path": str(save_path),
                    "file_name": file_name,
                }

                action = "Updated" if cached else "Downloaded"
                logger.info(f"  ✅ {action}: {file_name}")
                downloaded += 1

            except Exception as e:
                # Log and skip — a permissions error on one file shouldn't stop the sync.
                logger.error(f"  ❌ Skipped '{file_name}': {e}")
                errors += 1

        # Persist the updated manifest to disk for next run.
        state["drive"] = drive_state
        save_sync_state(state)

        logger.info(
            f"Google Drive sync complete — "
            f"{downloaded} downloaded/updated, {skipped} unchanged (skipped), {errors} errors."
        )

    except Exception as e:
        logger.error(f"Google Drive sync failed entirely: {e}")
        raise


# ===========================================================================
# MASTER SYNC ORCHESTRATOR
# ===========================================================================

def run_sync():
    """
    Master function that orchestrates the CV file sync from Google Drive (local only).

    Downloads CV files from the specified Google Drive folder.
    After a successful sync, writes a timestamp to data/last_sync.txt,
    which is displayed in the Streamlit sidebar.

    This function is called immediately on startup and then scheduled
    to run every night at 02:00 AM.
    """
    logger.info("=" * 60)
    logger.info(f"🔄 PAGie CV Sync (Local) started — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 Target folder: {GOOGLE_DRIVE_FOLDER_ID}")
    logger.info("=" * 60)

    logger.info("📂 Syncing CV files from Google Drive...")
    download_drive_files()

    # Persist a sync timestamp so the Streamlit UI can display it.
    with open(DATA_DIR / "last_sync.txt", "w") as f:
        f.write(datetime.now().isoformat())

    logger.info("=" * 60)
    logger.info("✅ PAGie CV Sync (Local) complete! Run data_science_eda.py to rebuild the knowledge base.")
    logger.info("=" * 60)


# ===========================================================================
# ENTRY POINT — Run once, then schedule nightly
# ===========================================================================

if __name__ == "__main__":
    # Run the sync immediately when the script is started.
    run_sync()

    # Schedule a nightly sync at 02:00 AM to keep the knowledge base fresh.
    schedule.every().day.at("02:00").do(run_sync)
    logger.info("📅 Nightly sync scheduled at 02:00 AM. Listening for next run...")

    # Keep the process alive to allow the scheduler to trigger.
    while True:
        schedule.run_pending()
        time.sleep(60)
