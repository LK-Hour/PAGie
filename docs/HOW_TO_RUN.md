# PAGie CV Analysis System - Complete User Guide

**Version:** 2.0 (CV-Focused)  
**Last Updated:** March 2026  
**Author:** PAGie Development Team

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Initial Setup](#initial-setup)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Using the CV Analysis System](#using-the-cv-analysis-system)
7. [Maintenance & Troubleshooting](#maintenance--troubleshooting)
8. [Advanced Topics](#advanced-topics)

---

## 1. Project Overview

**PAGie** (Personal AI Generation & Information Engine) is a Retrieval-Augmented Generation (RAG) system designed to analyze CVs/resumes from Google Drive. It uses:

- **Google Drive API** to sync CV files
- **Data Science techniques** (EDA, IQR filtering) to clean and process text
- **ChromaDB** for vector storage
- **LangChain** for RAG orchestration
- **Google Gemini or Ollama** for AI-powered question answering
- **Streamlit** for the web interface

### Key Features
✅ Automatic CV syncing from Google Drive  
✅ Intelligent text chunking with outlier removal  
✅ Semantic search across candidate profiles  
✅ Natural language queries (e.g., "Who has Python experience?")  
✅ Dual-mode operation (local Ollama or cloud Gemini)

---

## 2. System Requirements

### Hardware Requirements
- **RAM:** Minimum 4GB (8GB+ recommended)
  - For Ollama local model: 6GB+ RAM required
  - For Gemini API only: 4GB sufficient
- **Storage:** 5GB free space
  - Python environment: ~2GB
  - Ollama model (optional): 2.7GB
  - ChromaDB data: <100MB

### Software Requirements
- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows WSL2
- **Python:** Version 3.10 or higher
- **Internet:** Required for Google Drive sync and Gemini API

### API Access Required
1. **Google Drive API** (Mandatory)
   - Google Cloud Project with Drive API enabled
   - OAuth 2.0 credentials (client_secret.json)
   
2. **Google Gemini API** (Recommended for production)
   - Free tier: 60 requests/minute
   - Get key at: https://aistudio.google.com/apikey

3. **Ollama** (Optional for local inference)
   - Installation: https://ollama.com/download
   - Model: qwen3.5:0.8b (~1GB)

---

## 3. Initial Setup

### Step 1: Clone or Navigate to Project Directory
```bash
cd /path/to/pagie_project
```

### Step 2: Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages installed:**
- langchain, langchain-google-genai, langchain-chroma
- chromadb, sentence-transformers
- google-api-python-client, google-auth-httplib2
- streamlit, pandas, numpy, matplotlib, seaborn
- python-dotenv, schedule

### Step 4: Set Up Google Drive API

#### 4a. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (e.g., "PAGie-CV-System")
3. Enable **Google Drive API**:
   - APIs & Services → Enable APIs and Services
   - Search "Google Drive API" → Enable

#### 4b. Create OAuth 2.0 Credentials
1. Go to: APIs & Services → Credentials
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Configure consent screen:
   - User Type: External
   - App name: PAGie CV System
   - Scopes: Add `https://www.googleapis.com/auth/drive.readonly`
4. Create OAuth Client ID:
   - Application type: Desktop app
   - Name: PAGie Desktop Client
5. **Download JSON** and save as:
   ```
   client_secret_<YOUR-CLIENT-ID>.apps.googleusercontent.com.json
   ```
   Place this file in the project root directory.

#### 4c. Get Google Drive Folder ID
1. Open Google Drive in your browser
2. Navigate to the folder containing CV files
3. Copy the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/1mPmXrJbqbaxFkbpEbUKJlfYjUgbFKCpW
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            This is your FOLDER_ID
   ```

### Step 5: Get Google Gemini API Key (Production Mode)
1. Visit: https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the generated key (starts with `AIza...`)
4. Save for `.env` configuration

### Step 6: Install Ollama (Optional - For Local/Dev Mode)

**Only needed if you want to run locally without internet dependency.**

#### Linux Installation:
```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Add to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Start Ollama service
ollama serve > /tmp/ollama.log 2>&1 &

# Download model (2.7GB - requires ~4GB RAM to run)
ollama pull qwen3.5:0.8b
```

#### Verify Ollama Installation:
```bash
ollama list
# Should show: qwen3.5:0.8b    ~1 GB
```

**⚠️ Important:** The qwen3.5:0.8b model requires **~1.5GB RAM** to run. If your system has less available memory:
- Use Gemini API instead (production mode)
- Or use a smaller model: `ollama pull qwen:0.5b`

---

## 4. Configuration

### Create `.env` File

Copy the example and edit:
```bash
cp .env.example .env
nano .env  # or use any text editor
```

### Required Configuration

```env
# =====================================================
# 1. APP MODE - Choose your inference engine
# =====================================================
APP_MODE=prod
# Options:
#   - prod: Use Google Gemini API (recommended, requires internet)
#   - dev: Use local Ollama model (offline, requires 6GB+ RAM)

# =====================================================
# 2. GOOGLE DRIVE API (MANDATORY)
# =====================================================
# Path to your OAuth credentials file
GOOGLE_CLIENT_SECRET_FILE=client_secret_144832521505-xxxxx.apps.googleusercontent.com.json

# CV folder ID from Google Drive URL
GOOGLE_DRIVE_FOLDER_ID=1mPmXrJbqbaxFkbpEbUKJlfYjUgbFKCpW

# =====================================================
# 3. GOOGLE GEMINI API (for APP_MODE=prod)
# =====================================================
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Get your key at: https://aistudio.google.com/apikey

# =====================================================
# 4. NOTION API (DISABLED for CV-focused system)
# =====================================================
# Leave these blank - Notion integration removed
NOTION_TOKEN=
NOTION_DATABASE_IDS=
NOTION_PAGE_IDS=

# =====================================================
# 5. OLLAMA SETTINGS (for APP_MODE=dev)
# =====================================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:0.8b

# =====================================================
# 6. DATA PATHS
# =====================================================
RAW_DATA_DIR=./data/raw_files
CHROMA_DB_PATH=./chroma_db
EDA_REPORT_PATH=./assets/eda_report.png
```

### Configuration Tips

**For Production Use (Recommended):**
```env
APP_MODE=prod
GOOGLE_API_KEY=<your-gemini-key>
GOOGLE_DRIVE_FOLDER_ID=<your-cv-folder-id>
```

**For Local Development (Offline):**
```env
APP_MODE=dev
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3.5:0.8b
```

---

## 5. Running the System

### 🚀 Quick Start (All-in-One)

The easiest way to run PAGie is using the provided scripts:

#### For Production (Gemini API):
```bash
# Make script executable (first time only)
chmod +x ops_run_prod_gemini.sh

# Run the full pipeline
./ops_run_prod_gemini.sh
```

This script will:
1. ✅ Activate virtual environment
2. ✅ Sync CV files from Google Drive
3. ✅ Build knowledge base with data science processing
4. ✅ Launch Streamlit UI

#### For Development (Local Ollama):
```bash
# Make script executable (first time only)
chmod +x ops_run_dev_local.sh

# Ensure Ollama is running first
ollama serve > /tmp/ollama.log 2>&1 &

# Run with local model
./ops_run_dev_local.sh
```

---

### 📦 Step-by-Step Manual Execution

If you prefer to run each step manually:

#### Step 1: Activate Virtual Environment
```bash
source venv/bin/activate
```

#### Step 2: Sync CV Files from Google Drive

```bash
python sync_data.py
```

**First-time authentication:**
- Browser will open automatically
- Sign in with your Google account
- Click "Allow" to grant Drive access
- Token saved to `token.json` (reused for future syncs)

**Expected output:**
```
2026-03-30 - sync_data - INFO - Starting PAGie data sync...
2026-03-30 - sync_data - INFO - Google Drive folder ID: 1mPmXrJbqbaxFkbpEbUKJlfYjUgbFKCpW
2026-03-30 - sync_data - INFO - Found 3 files to sync from Google Drive (folder-scoped)
2026-03-30 - sync_data - INFO - ✓ Downloaded: KIMHOUR_LOEM_CV.pdf (123 KB)
2026-03-30 - sync_data - INFO - ✓ Downloaded: Luy_Virak_CV.pdf (456 KB)
2026-03-30 - sync_data - INFO - ✓ Downloaded: LY_KIMKHENG_CV.pdf (789 KB)
2026-03-30 - sync_data - INFO - Data sync complete! 3 files synced successfully.
```

**Troubleshooting sync:**
- ❌ "Invalid folder ID" → Check `GOOGLE_DRIVE_FOLDER_ID` in .env
- ❌ "Permission denied" → Ensure folder is shared with your Google account
- ❌ "No files found" → Verify folder contains PDF/DOCX files

#### Step 3: Build Knowledge Base (Data Science Pipeline)

```bash
python data_science_eda.py
```

**What this does:**
1. Loads CV files from `./data/raw_files/`
2. Chunks text into 500-character segments
3. Calculates word count statistics
4. Applies **IQR (Interquartile Range)** filtering to remove:
   - Too-short chunks (< 5 words)
   - Statistical outliers (noise, headers, footers)
5. Generates embeddings using `sentence-transformers/all-MiniLM-L6-v2`
6. Stores vectors in ChromaDB
7. Creates EDA visualization plot

**Expected output:**
```
2026-03-30 - data_science_eda - INFO - Starting PAGie knowledge base build...
2026-03-30 - data_science_eda - INFO - Loaded 3 CV documents (679 raw chunks)
2026-03-30 - data_science_eda - INFO - IQR Analysis: Q1=39.0, Q3=69.0 words
2026-03-30 - data_science_eda - INFO - Filtered 18 outlier chunks (2.7%)
2026-03-30 - data_science_eda - INFO - Final dataset: 661 clean chunks
2026-03-30 - data_science_eda - INFO - Generating embeddings (384-dimensional vectors)...
2026-03-30 - data_science_eda - INFO - ✓ ChromaDB populated: 661 chunks indexed
2026-03-30 - data_science_eda - INFO - ✓ EDA report saved: ./assets/eda_report.png
```

**Verify ChromaDB:**
```bash
ls -lh chroma_db/
# Should show ~5MB of data
```

**View EDA Report:**
```bash
# Linux with GUI
xdg-open assets/eda_report.png

# macOS
open assets/eda_report.png
```

#### Step 4: Launch Streamlit UI

```bash
streamlit run app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

**Access the UI:**
- Open browser → `http://localhost:8501`
- Streamlit UI will load with "PAGie CV Analysis System" title

---

## 6. Using the CV Analysis System

### Web Interface Overview

![PAGie UI]

#### Sidebar (Left Panel)
- **System Status:** Shows database statistics
  - Number of CVs indexed
  - Total chunks in knowledge base
  - Last sync timestamp
- **About:** System information and tech stack

#### Main Chat Interface
- **Welcome Message:** Instructions and example queries
- **Chat Input:** Type your questions at the bottom
- **Response Area:** AI-generated answers with source citations

### Example Queries

#### 1. Find Candidates by Skills
```
Q: Who has Python programming experience?

A: The following candidates have Python experience:
   1. KIMHOUR LOEM - Listed Python in technical skills section
   2. Luy Virak - 3 years of Python development in work history
   
   Sources: KIMHOUR_LOEM_CV.pdf (Page 1), Luy_Virak_CV.pdf (Page 2)
```

#### 2. Search by Education
```
Q: Which candidates have a Master's degree?

A: Candidate LY KIMKHENG holds an MBA from National University of 
   Management, graduated in 2020.
   
   Sources: LY_KIMKHENG_CV.pdf (Page 1)
```

#### 3. Find by Experience Level
```
Q: Show me software engineers with more than 5 years of experience

A: Based on the work history sections, the following candidates have 
   5+ years of software engineering experience:
   - Luy Virak: 6 years (2018-present) as Full Stack Developer...
```

#### 4. Skill Matching
```
Q: Who knows both React and Node.js?

A: Candidate KIMHOUR LOEM has listed both React.js and Node.js in 
   their technical skills section...
```

#### 5. General Queries
```
Q: List all candidates in the database

A: The knowledge base contains CVs for the following candidates:
   1. KIMHOUR LOEM
   2. Luy Virak
   3. LY KIMKHENG
```

### Tips for Better Results

✅ **Do's:**
- Be specific: "Python experience" not just "programming"
- Ask one thing at a time: Break complex queries into parts
- Use job titles: "software engineer", "data scientist", "project manager"
- Reference skills explicitly: "machine learning", "AWS", "SQL"

❌ **Don'ts:**
- Avoid vague queries: "Tell me everything" (too broad)
- Don't ask for comparisons without context: "Who's better?" (subjective)
- Avoid personal opinions: "Do you like this candidate?" (AI can't have preferences)

### Understanding Responses

**Source Citations:**
Every answer includes source references like:
```
Sources: KIMHOUR_LOEM_CV.pdf, Luy_Virak_CV.pdf
```
This shows which CV files were used to generate the answer.

**Confidence Indicators:**
- "Candidate has..." → Found in CV text
- "Based on the work history..." → Inferred from context
- "No information found..." → Not in knowledge base

---

## 7. Maintenance & Troubleshooting

### Updating CV Data

When you add/remove CV files in Google Drive:

```bash
# 1. Re-sync from Google Drive
python sync_data.py

# 2. Rebuild knowledge base
python data_science_eda.py

# 3. Restart Streamlit (Ctrl+C, then rerun)
streamlit run app.py
```

**Quick reset and rebuild:**
```bash
chmod +x ops_backup_reset_rebuild.sh
./ops_backup_reset_rebuild.sh
```
This script:
- Backs up current database to `backups/`
- Clears `data/raw_files/` and `chroma_db/`
- Re-syncs and rebuilds everything

---

### Common Issues & Solutions

#### Issue 1: "Gemini API Quota Exceeded (429)"
```
Error: Resource has been exhausted (e.g. check quota)
```

**Solution:**
- **Wait:** Gemini free tier resets daily (60 requests/minute)
- **Switch to Ollama:** Change `APP_MODE=dev` in `.env` and restart
- **Upgrade:** Get Gemini paid tier for higher limits

---

#### Issue 2: "Ollama Model Out of Memory"
```
Error: model requires more system memory (3.8 GiB) than is available
```

**Solution:**
1. **Free up RAM:**
   ```bash
   # Check memory usage
   free -h
   
   # Close heavy applications (browser tabs, IDEs, etc.)
   ```

2. **Use smaller model:**
   ```bash
   # Download lightweight alternative (0.5GB)
   ollama pull qwen:0.5b
   
   # Update .env
   OLLAMA_MODEL=qwen:0.5b
   ```

3. **Use Gemini instead:**
   ```bash
   # Switch to cloud API
   APP_MODE=prod
   ```

---

#### Issue 3: "No module named 'langchain'"
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

#### Issue 4: "ChromaDB Empty / No Results"
```
Connected to ChromaDB at ./chroma_db with 0 chunks
```

**Solution:**
```bash
# Knowledge base not built yet
python data_science_eda.py

# Verify database
du -sh chroma_db/
# Should show ~5MB
```

---

#### Issue 5: "Google Drive Folder Not Found"
```
Error: Folder ID '1mPm...' is invalid or not accessible
```

**Solution:**
1. Verify folder ID from URL
2. Check folder sharing permissions:
   - Right-click folder → Share
   - Add your Google account email
   - Role: Viewer or Editor
3. Update `.env` with correct `GOOGLE_DRIVE_FOLDER_ID`

---

#### Issue 6: "Token Expired / Authentication Failed"
```
Error: invalid_grant: Token has been expired or revoked
```

**Solution:**
```bash
# Delete old token
rm token.json

# Re-run sync (will prompt for authentication)
python sync_data.py
```

---

### System Health Checks

Run these commands to verify system status:

```bash
# 1. Check Python environment
which python
python --version  # Should be 3.10+

# 2. Check Ollama service (if using dev mode)
ps aux | grep ollama
curl http://localhost:11434  # Should respond

# 3. Check ChromaDB size
du -sh chroma_db/  # Should be ~5MB if populated

# 4. Check synced files
ls -lh data/raw_files/  # Should show CV PDFs

# 5. Verify dependencies
pip list | grep -E "langchain|chromadb|streamlit|google"
```

---

## 8. Advanced Topics

### Nightly Automatic Sync

To keep CVs up-to-date automatically, use the built-in scheduler:

```python
# Already included in sync_data.py
# Syncs at 2 AM daily when left running

# Run as background process
nohup python sync_data.py > sync.log 2>&1 &
```

Or use system cron:
```bash
# Edit crontab
crontab -e

# Add daily sync at 2 AM
0 2 * * * cd /path/to/pagie_project && ./venv/bin/python sync_data.py >> sync.log 2>&1
```

---

### Adjusting Chunk Size

For different CV formats, you might need to adjust chunking:

**Edit `data_science_eda.py`:**
```python
# Line ~141
text_splitter = CharacterTextSplitter(
    chunk_size=500,        # Increase for longer context
    chunk_overlap=50,      # Increase for better continuity
    separator="\n"
)
```

**Guidelines:**
- **500-800 chars:** Good for CVs/resumes
- **1000-1500 chars:** Better for long-form documents
- **Overlap 10%:** Standard (50 chars for 500 chunk size)

After changing, rebuild:
```bash
./ops_backup_reset_rebuild.sh
```

---

### Customizing System Prompts

To change how the AI responds, edit `rag_pipeline.py`:

```python
# Line ~109 - System prompt
SYSTEM_PROMPT = """
You are a CV Analysis Assistant...
[Customize this section for different tone/format]
"""
```

Examples:
- **Formal tone:** "You are a professional recruiter..."
- **Casual tone:** "You are a friendly HR assistant..."
- **Structured format:** "Always respond in bullet points..."

---

### Adding More Data Sources

Currently supports Google Drive only. To add more sources:

1. **Implement new loader in `sync_data.py`:**
   ```python
   def sync_from_dropbox():
       # Your Dropbox API logic
       pass
   ```

2. **Add to main sync flow:**
   ```python
   def sync_all_data():
       sync_from_google_drive()
       sync_from_dropbox()  # New source
   ```

3. **Update documentation**

---

### Performance Tuning

**For faster searches:**
```python
# In rag_pipeline.py, adjust retrieval count
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}  # Lower = faster, higher = more context
)
```

**For better accuracy:**
```python
# Increase context chunks
search_kwargs={"k": 10}  # More chunks = better accuracy, slower
```

---

### Backup Strategy

**Automated backups:**
```bash
# Run backup script
./ops_backup_reset_rebuild.sh  # Creates backup before reset
```

**Manual backup:**
```bash
# Backup ChromaDB
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup synced files
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

**Restore from backup:**
```bash
# Extract ChromaDB
tar -xzf chroma_backup_20260330.tar.gz

# Verify
du -sh chroma_db/
```

---

## Summary: Quick Reference Commands

```bash
# === SETUP (One-time) ===
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# (Edit .env with your API keys)

# === REGULAR USE ===
# Option A: Production mode (Gemini API)
./ops_run_prod_gemini.sh

# Option B: Development mode (Local Ollama)
ollama serve > /tmp/ollama.log 2>&1 &
./ops_run_dev_local.sh

# === MAINTENANCE ===
# Update data
python sync_data.py
python data_science_eda.py

# Reset and rebuild
./ops_backup_reset_rebuild.sh

# === TROUBLESHOOTING ===
# Check system status
free -h                    # Memory
ollama list               # Local models
du -sh chroma_db/         # Database size
pip list | grep langchain # Dependencies
```

---

## Support & Resources

- **Project Documentation:** See `README.md` and `CV_FOCUSED_UPDATE.md`
- **Quick Start Guide:** See `QUICK_START_CV.md`
- **Deployment Status:** See `DEPLOY_STATUS.md`
- **Google Drive API:** https://developers.google.com/drive
- **Gemini API:** https://ai.google.dev/docs
- **Ollama Documentation:** https://ollama.com/docs
- **LangChain Docs:** https://python.langchain.com/

---

**🎓 Academic Project by CADT Data Science Students**

For questions or issues, refer to the project documentation or contact the development team.

*Last updated: March 2026*
