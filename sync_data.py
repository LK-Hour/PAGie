"""
sync_data.py — Smart ETL Pipeline for PAGie (CV-Focused)
========================================================
This is the Extract-Transform-Load (ETL) script that forms the foundation
of PAGie's CV analysis system. It connects to a specific Google Drive folder
containing CV/Resume files:

  Google Drive API  → Downloads PDFs and Google Docs from a designated folder.

**Smart Sync (Incremental):**
  A sync-state manifest is persisted at ./data/sync_state.json. Each entry
  records the remote modification timestamp of every file downloaded.
  On subsequent runs, only files whose remote timestamp has changed (or that
  are brand-new) are re-downloaded, dramatically cutting API usage and time.
  Locally saved files that no longer exist in the source are also removed.

All downloaded CV files are saved to the ./data/drive/ directory for processing
by data_science_eda.py. A nightly schedule runs this automatically at 02:00 AM.

Usage:
  python sync_data.py          # Runs once immediately, then schedules nightly
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
# We download documents and PDFs which are the most common CV formats.
SUPPORTED_MIME_TYPES = [
    "application/vnd.google-apps.document",       # Google Docs
    "application/pdf",                            # PDFs
    "text/plain",                                 # Plain text files
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
]

# REQUIRED: Specific Google Drive folder ID containing CV files
# Set in .env as GOOGLE_DRIVE_FOLDER_ID
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

# Sync-state manifest — records the last-known modification timestamp for every
# synced file/page so unchanged content is skipped on future runs.
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

    The manifest is a JSON dict with two top-level keys:
      - "drive": maps Drive file IDs  → {"modified_time": str, "local_path": str, "file_name": str}
      - "notion": maps Notion page IDs → {"last_edited_time": str, "local_path": str, "title": str}

    Returns:
        The manifest dict, or an empty skeleton if no state file exists yet.
    """
    if SYNC_STATE_FILE.exists():
        try:
            with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read sync state ({e}). Starting fresh.")
    return {"drive": {}, "notion": {}}


def save_sync_state(state: dict) -> None:
    """
    Persists the sync-state manifest to disk after every sync run.

    Args:
        state: The full manifest dict (both "drive" and "notion" sections).
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
    Authenticates with the Google Drive API using OAuth 2.0.

    On first run, this opens a browser window for the user to grant permission.
    The resulting token is saved to token.json so subsequent runs are silent.
    
    On Streamlit Cloud, this function will raise an error since sync requires local auth.

    Returns:
        A Google Drive API service object ready to make requests.

    Raises:
        FileNotFoundError: If no client_secret_*.json file exists in the project root.
        RuntimeError: If running on Streamlit Cloud where sync is not available.
    """
    # Check if running on Streamlit Cloud
    force_local_mode = os.getenv("FORCE_LOCAL_MODE", "false").lower() == "true"
    if not force_local_mode:
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                # Running on Streamlit Cloud - sync not available
                raise RuntimeError(
                    "Google Drive sync is not available on Streamlit Cloud. "
                    "For cloud deployment, pre-upload CV files to the repository or use GCS sync."
                )
        except (ImportError, AttributeError):
            pass  # Not on Streamlit, continue with normal auth
    
    creds = None

    # Attempt to load a previously saved OAuth token to avoid re-authentication.
    if os.path.exists(TOKEN_FILE):
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

        # Persist the token so we don't need to re-authenticate next run.
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        logger.info("Google OAuth token saved to token.json.")

    return build("drive", "v3", credentials=creds)


def _list_all_drive_files(service) -> list:
    """
    Retrieves every supported file from the entire Google Drive account.

    Uses the Drive API's pagination (nextPageToken) to handle accounts
    with more than 1000 files. Only files matching SUPPORTED_MIME_TYPES
    are returned — images, videos, and spreadsheets are ignored since
    they cannot be meaningfully converted to RAG text chunks.

    Args:
        service: An authenticated Google Drive API service object.

    Returns:
        A flat list of file metadata dicts: {id, name, mimeType}.
    """
    # Build a MIME type filter — only fetch file types we can process as text.
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
        # Request the next page of results (max 1000 per call).
        # modifiedTime is fetched so we can skip files that haven't changed.
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

        # If there's another page, continue; otherwise stop.
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return all_files


def download_drive_files():
    """
    Smart-syncs supported files from the entire Google Drive account.

    Uses the local sync-state manifest (data/sync_state.json) to record each
    file's ``modifiedTime``. On each run the following logic is applied per file:

      - **New files** (not in the manifest) are downloaded.
      - **Modified files** (remote modifiedTime != cached value) are re-downloaded.
      - **Unchanged files** (same modifiedTime + local file exists) are skipped,
        saving API quota and time.
      - **Deleted files** (in manifest but no longer on Drive) are removed from
        disk and the manifest to keep the knowledge base clean.

    Supported file types:
      - Google Docs        → exported as plain text (.txt)
      - Google Slides      → exported as plain text (.txt)
      - PDFs               → downloaded directly (.pdf)
      - Plain text files   → downloaded directly (.txt)

    Files that fail to download are skipped with an error log so a single
    bad file does not block the entire sync.
    """
    try:
        service = get_google_drive_service()

        # Retrieve every supported file across the entire account (includes modifiedTime).
        files = _list_all_drive_files(service)
        logger.info(f"Found {len(files)} supported file(s) across entire Google Drive.")

        # Load the persisted sync state to compare timestamps.
        state = load_sync_state()
        drive_state = state.get("drive", {})

        # Build a set of current remote file IDs to detect files deleted from Drive.
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
# NOTION — Page Fetching
# ===========================================================================

def fetch_notion_pages():
    """
    Smart-syncs ALL pages the PAGie integration has access to via the Notion Search API.

    Uses the sync-state manifest (data/sync_state.json) to record each page's
    ``last_edited_time``. On each run the following logic is applied per page:

      - **New pages** (not in manifest) are downloaded.
      - **Edited pages** (remote last_edited_time != cached value) are re-downloaded.
      - **Unchanged pages** are skipped entirely — no block-content API calls are made,
        saving quota and time.
      - **Deleted pages** (in manifest but no longer returned by Search) are removed
        from disk and the manifest to keep the knowledge base clean.

    How to share pages with the integration:
      1. Open any Notion page or database you want PAGie to know about.
      2. Click the "..." menu (top-right) → "Add connections".
      3. Search for and select your PAGie integration.
      4. Repeat for every page/database you want indexed.

    Each page is saved as a .txt file to ./data/notion/.

    Note: Supports both legacy token format (secret_...) and new format (ntn_...).
    """
    if not NOTION_TOKEN:
        logger.warning("NOTION_TOKEN not set in .env. Skipping Notion sync.")
        return

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    try:
        # Use the Search API to find ALL pages/databases shared with this integration.
        # This is more robust than querying a specific database ID.
        all_pages = []
        start_cursor = None

        logger.info("Searching for all Notion pages shared with this integration...")

        while True:
            payload = {"filter": {"value": "page", "property": "object"}, "page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            response = requests.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            all_pages.extend(data.get("results", []))

            # Paginate through all results if there are more than 100 pages.
            if data.get("has_more"):
                start_cursor = data.get("next_cursor")
            else:
                break

        logger.info(f"Found {len(all_pages)} Notion page(s) shared with the integration.")

        if not all_pages:
            logger.warning(
                "⚠️  No Notion pages found. Make sure you have shared your pages/databases "
                "with the PAGie integration via Notion's 'Add connections' menu."
            )
            return

        # Load the persisted sync state to compare edit timestamps.
        state = load_sync_state()
        notion_state = state.get("notion", {})

        # Build a set of current remote page IDs to detect deleted pages.
        remote_page_ids = {p["id"] for p in all_pages}

        # --- Cleanup: remove local files for pages deleted from Notion ---
        stale_ids = [pid for pid in list(notion_state.keys()) if pid not in remote_page_ids]
        for pid in stale_ids:
            entry = notion_state.pop(pid)
            stale_path = Path(entry.get("local_path", ""))
            if stale_path.exists():
                stale_path.unlink()
                logger.info(f"  🗑️  Removed stale page: {stale_path.name}")

        saved = 0
        skipped = 0
        errors = 0

        for page in all_pages:
            page_id = page["id"]
            title = _extract_page_title(page)
            # Notion exposes last_edited_time at the top level of every page object.
            remote_edited = page.get("last_edited_time", "")

            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            save_path = NOTION_DIR / f"{safe_title or page_id}.txt"

            # --- Smart-skip: only re-fetch if the page was edited or is missing locally ---
            cached = notion_state.get(page_id, {})
            if cached.get("last_edited_time") == remote_edited and save_path.exists():
                logger.debug(f"  ⏭️  Unchanged, skipping: {title}")
                skipped += 1
                continue

            try:
                # Fetch ALL block content recursively (handles nested pages/lists).
                blocks = _fetch_all_blocks(page_id, headers)

                # Convert Notion blocks into plain text.
                text_content = _extract_text_from_blocks(blocks)

                if text_content.strip():
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(f"Title: {title}\nSource: Notion\n\n{text_content}")

                    # Record the new timestamp and local path in the manifest.
                    notion_state[page_id] = {
                        "last_edited_time": remote_edited,
                        "local_path": str(save_path),
                        "title": title,
                    }

                    action = "Updated" if cached else "Saved"
                    logger.info(f"  ✅ {action}: {title}")
                    saved += 1
                else:
                    logger.warning(f"  ⚠️  Skipping empty page: {title}")

            except Exception as e:
                logger.error(f"  ❌ Failed to fetch page '{title}': {e}")
                errors += 1

        # Persist the updated manifest to disk for next run.
        state["notion"] = notion_state
        save_sync_state(state)

        logger.info(
            f"Notion sync complete — "
            f"{saved} saved/updated, {skipped} unchanged (skipped), {errors} errors."
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Notion sync failed: {e}")
        raise


def _extract_page_title(page: dict) -> str:
    """
    Extracts the plain text title from a Notion page object.

    Notion stores the title under a property of type 'title', but the property
    key name can differ (e.g., 'Name', 'Title', 'Task'). This function searches
    all properties for one of type 'title'.

    Args:
        page: A Notion page object from the API response.

    Returns:
        The plain text title string, or the page ID as a fallback.
    """
    properties = page.get("properties", {})
    for prop_value in properties.values():
        if prop_value.get("type") == "title":
            title_arr = prop_value.get("title", [])
            if title_arr:
                return title_arr[0].get("plain_text", "Untitled")
    return page.get("id", "Untitled")


def _fetch_all_blocks(block_id: str, headers: dict, depth: int = 0, max_depth: int = 5) -> list:
    """
    Recursively fetch all blocks (including nested children) for a given block/page ID.
    """
    if depth > max_depth:
        return []
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    while url:
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for block in data.get("results", []):
                blocks.append(block)
                if block.get("has_children"):
                    child_blocks = _fetch_all_blocks(block["id"], headers, depth + 1, max_depth)
                    blocks.extend(child_blocks)
            # Handle pagination
            if data.get("has_more"):
                url = f"https://api.notion.com/v1/blocks/{block_id}/children?start_cursor={data['next_cursor']}"
            else:
                url = None
        except Exception as e:
            logger.warning(f"Failed to fetch children for block {block_id}: {e}")
            break
    return blocks


def _extract_text_from_blocks(blocks: list) -> str:
    """
    Converts a list of Notion block objects into a flat plain text string.

    Handles the most common block types including nested children:
      paragraph, heading_1/2/3, bulleted_list_item,
      numbered_list_item, to_do, quote, callout, code, table, toggle.

    Args:
        blocks: A list of Notion block objects from the blocks API.

    Returns:
        A newline-separated string of all text content.
    """
    text_lines = []
    for block in blocks:
        block_type = block.get("type", "")
        block_data = block.get(block_type, {})

        # Most content blocks have a 'rich_text' array containing the text.
        rich_text = block_data.get("rich_text", [])
        if rich_text:
            plain = " ".join([rt.get("plain_text", "") for rt in rich_text])
            if plain.strip():
                text_lines.append(plain)
        # Handle table rows
        elif block_type == "table_row":
            cells = block_data.get("cells", [])
            row_texts = []
            for cell in cells:
                cell_text = " ".join([rt.get("plain_text", "") for rt in cell])
                row_texts.append(cell_text)
            if any(row_texts):
                text_lines.append(" | ".join(row_texts))
        # Handle dividers and blank lines for structure
        elif block_type == "divider":
            text_lines.append("---")

    return "\n".join(line for line in text_lines if line)


# ===========================================================================
# MASTER SYNC ORCHESTRATOR
# ===========================================================================

def run_sync():
    """
    Master function that orchestrates the CV file sync from Google Drive.

    Downloads CV files from the specified Google Drive folder.
    After a successful sync, writes a timestamp to data/last_sync.txt,
    which is displayed in the Streamlit sidebar.

    This function is called immediately on startup and then scheduled
    to run every night at 02:00 AM.
    """
    logger.info("=" * 60)
    logger.info(f"🔄 PAGie CV Sync started — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 Target folder: {GOOGLE_DRIVE_FOLDER_ID}")
    logger.info("=" * 60)

    logger.info("📂 Syncing CV files from Google Drive...")
    download_drive_files()

    # Persist a sync timestamp so the Streamlit UI can display it.
    with open(DATA_DIR / "last_sync.txt", "w") as f:
        f.write(datetime.now().isoformat())

    logger.info("=" * 60)
    logger.info("✅ PAGie CV Sync complete! Run data_science_eda.py to rebuild the knowledge base.")
    logger.info("=" * 60)
    
    # Sync ChromaDB to cloud after data update (for cloud deployment)
    try:
        from gcs_sync import auto_sync_after_update
        auto_sync_after_update()
    except ImportError:
        logger.warning("gcs_sync module not found - skipping cloud sync")
    except Exception as e:
        logger.error(f"Failed to sync ChromaDB to cloud: {e}")


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
