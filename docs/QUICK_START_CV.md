# PAGie CV Analysis System - Quick Start Guide

## 🎯 What This System Does

PAGie analyzes CV/Resume files from a Google Drive folder and answers questions about candidates using AI.

## 📋 Prerequisites

1. Python 3.10+
2. Google Drive API credentials (`client_secret_*.json` file)
3. Google Gemini API key
4. CV files stored in a Google Drive folder

## ⚙️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file:
```bash
# Required: Your CV folder ID from Google Drive
GOOGLE_DRIVE_FOLDER_ID=1mPmXrJbqbaxFkbpEbUKJlfYjUgbFKCpW

# Required: Gemini API key
GOOGLE_API_KEY=your_api_key_here

# Model selection
GEMINI_MODEL=gemini-2.0-flash-lite
APP_MODE=prod  # or 'dev' for local LLM
```

### 3. First-Time Google Drive Authentication
```bash
python sync_data.py
```
- A browser window will open
- Grant permission to access Google Drive
- `token.json` will be saved for future runs

## 🚀 Usage

### Option 1: Web Interface (Recommended)

#### Production Mode (Gemini)
```bash
./ops_run_prod_gemini.sh
```

#### Development Mode (Local LLM)
```bash
./ops_run_dev_local.sh
```

Then open your browser to the Streamlit URL (usually http://localhost:8501)

### Option 2: Manual Step-by-Step

1. **Sync CV files:**
   ```bash
   python sync_data.py
   ```

2. **Build knowledge base:**
   ```bash
   python data_science_eda.py
   ```

3. **Launch chatbot:**
   ```bash
   streamlit run app.py
   ```

## 💬 Example Queries

### Finding Candidates by Skills
```
"Who has Python experience?"
"List candidates who know machine learning"
"Find someone with React and Node.js skills"
```

### Finding by Education
```
"Who has an MBA?"
"List all candidates with master's degrees"
"Find candidates who studied computer science"
```

### Finding by Experience
```
"Who has 5+ years of experience?"
"List candidates who worked at Google"
"Find senior software engineers"
```

### Finding by Location/Other
```
"Who is based in San Francisco?"
"List candidates with project management experience"
"Find bilingual candidates"
```

## 📊 Understanding the Results

Each answer includes:
- **Summary:** Direct answer to your question
- **Candidate Details:** Specific information from their CVs
- **Sources:** Which CV files were referenced (shown as badges)

Example response:
```
Summary: 3 candidates have Python experience.

Candidate Details:
• John Smith - 5 years Python experience, worked at Google on ML projects
• Jane Doe - 3 years Python, data science and analytics focus
• Robert Chen - 2 years Python for backend development

Sources: [📄 john_smith_cv.pdf] [📄 jane_doe_resume.pdf] [📄 robert_chen.docx]
```

## 🔧 Troubleshooting

### "GOOGLE_DRIVE_FOLDER_ID is required"
- Make sure `.env` has the folder ID set
- Check that the folder ID is correct (find it in the Google Drive URL)

### "No CV files found"
- Run `python sync_data.py` first
- Check that the folder has CV files (PDF, DOCX, or Google Docs)
- Verify you have read permission on the folder

### "ChromaDB connection failed"
- Run `python data_science_eda.py` to build the database
- Check that `./chroma_db/` directory exists

### Gemini API Quota Exceeded
- Switch to dev mode: Set `APP_MODE=dev` in `.env`
- Or wait for the daily quota to reset

## 🔄 Updating the CV Database

When new CVs are added to the Google Drive folder:

1. **Sync:** Click "Sync CV Files" in the UI or run `python sync_data.py`
2. **Rebuild:** Click "Rebuild Knowledge Base" or run `python data_science_eda.py`
3. New CVs are now searchable!

## 📈 Viewing Analytics

The EDA report shows:
- CV content distribution
- Word count statistics
- Quality filtering results
- Top CV files by data volume

View it in the sidebar of the Streamlit app or at `./assets/eda_report.png`

## 🛠️ Advanced: Reset Everything

If you need to start fresh:
```bash
./ops_backup_reset_rebuild.sh
```

This will:
- Backup the current database
- Clear all cached data
- Re-sync from Google Drive
- Rebuild embeddings from scratch

## 💡 Tips for Best Results

1. **Be specific:** "Python developers with 5+ years" works better than "good developers"
2. **Use CV terminology:** Skills, experience, education, projects, certifications
3. **Ask follow-ups:** PAGie maintains conversation context
4. **Check sources:** Always verify which CVs were referenced

## 📚 System Components

- `sync_data.py` - Downloads CVs from Google Drive
- `data_science_eda.py` - Processes and analyzes CV text
- `rag_pipeline.py` - Handles search and answer generation
- `app.py` - Web interface

## 🎓 Academic Project Info

This is a Data Science project for CADT (Cambodia Academy of Digital Technology).

**Key Technologies:**
- LangChain for RAG orchestration
- ChromaDB for vector storage
- Gemini 3.0 for answer generation
- Pandas/NumPy for data science
- Streamlit for UI

**Data Science Techniques:**
- Exploratory Data Analysis (EDA)
- Interquartile Range (IQR) outlier filtering
- Semantic text chunking
- Vector embeddings

---

**Need help?** Check `CV_FOCUSED_UPDATE.md` for detailed change documentation.
