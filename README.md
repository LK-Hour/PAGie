# PAGie: Personal AI Generation & Information Engine

**An Intelligent CV Analysis RAG System using Google Drive and Gemini 3.0**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-green)
![Gemini](https://img.shields.io/badge/Google_Gemini-3.0-orange)
![Data_Science](https://img.shields.io/badge/Data_Science-EDA_%26_IQR-purple)

## 📖 Project Overview
**PAGie** is a specialized AI assistant developed for an academic Data Science & Software Engineering project at CADT. It focuses on analyzing **CV/Resume files** stored in a specific Google Drive folder, applying rigorous Data Science cleaning techniques, and using **Retrieval-Augmented Generation (RAG)** to answer questions about candidate profiles with high precision.

### ✨ Key Features
* **Focused ETL Pipeline:** Automatically fetches CV files (PDFs, Docs) from a designated Google Drive folder.
* **Data Science Preprocessing:** Applies **Exploratory Data Analysis (EDA)** and the **Interquartile Range (IQR)** statistical method to detect and remove extreme text-chunk outliers, ensuring highly optimized LLM context.
* **Advanced RAG Architecture:** Utilizes local Sentence-Transformers embeddings and **ChromaDB** for rapid vector similarity search.
* **Gemini 3.0 Integration:** Leverages Google's native multimodal LLM for accurate, hallucination-free answer generation about CV content.
* **Automated Sync:** Intelligent incremental sync keeps the CV knowledge base up to date.
* **Streamlit UI:** A clean, intuitive chat interface for querying candidate information.

---

## 🛠️ Technology Stack
* **Language:** Python
* **Orchestration:** LangChain
* **LLM (Prod):** Google AI Studio (Gemini)
* **LLM (Dev):** Local Ollama model (`qwen3.5:0.8b`)
* **Embeddings:** Local Sentence-Transformers (`all-MiniLM-L6-v2`)
* **Vector Database:** ChromaDB
* **Data Extraction:** Google Drive API (scoped to specific CV folder)
* **Data Science:** Pandas, NumPy, Matplotlib, Seaborn
* **Frontend UI:** Streamlit

---

## 🏠 Two App Versions: Local vs Cloud

PAGie now has **two separate app versions** for different use cases:

### `app_local.py` - Local Development (Recommended for Development)
**Use this when:** Running on your local machine

✅ **Features:**
- Pure local paths (`./chroma_db`, `./cache`, `./assets`)
- Google Drive OAuth sync (browser authentication)
- Full Ollama support for local LLM
- No cloud detection logic (simple, clean code)
- Fast iteration and testing

```bash
# Run local version
streamlit run app_local.py
```

### `app.py` - Cloud Deployment (For Streamlit Cloud)
**Use this when:** Deploying to Streamlit Cloud

✅ **Features:**
- Auto-detects cloud environment
- Uses `/tmp` paths on cloud (writable)
- Pre-committed CV files from repository
- Optional GCS bucket for persistence
- Automatic Gemini fallback

```bash
# Deploy this to Streamlit Cloud
streamlit run app.py
```

📖 **Full comparison guide:** See [`docs/LOCAL_VS_CLOUD.md`](docs/LOCAL_VS_CLOUD.md)

---

## 🚀 Runtime Modes (Dev vs Prod)

PAGie supports two runtime modes via `.env`:

- `APP_MODE=dev` → Local LLM via Ollama (no Gemini rate-limit interruptions during development)
- `APP_MODE=prod` → Gemini (for final demo/report alignment with project proposal)

### ⚡ **High-Performance Mode (Recommended)**
Optimized versions with model caching and faster responses:

**Dev (local LLM - Optimized):**
```bash
./ops_run_optimized_dev.sh
```

**Prod (Gemini - Optimized):**
```bash
./ops_run_optimized_prod.sh
```

### 🐢 **Legacy Mode**
Original versions (kept for comparison):

**Dev (local LLM):**
```bash
./ops_run_dev_local.sh
```

**Prod (Gemini):**
```bash
./ops_run_prod_gemini.sh
```

### 🔧 **Maintenance Commands**
```bash
# Backup + Reset noisy DB + Rebuild vectors
./ops_backup_reset_rebuild.sh

# Test performance improvements
python test_performance.py
```

---

## ⚡ **Performance Optimizations** 

PAGie now includes high-performance versions that address the main bottlenecks:

### 🚀 **Speed Improvements:**
- **Model Pre-loading**: AI models load once at startup (8s → instant subsequent queries)
- **Embedding Caching**: Query embeddings cached to disk (~2.6s → ~0.1s for similar queries)
- **Singleton Pattern**: Models stay loaded in memory between queries
- **Optimized Context**: Reduced context size for faster LLM processing
- **Streamlined Pipeline**: Minimal overhead in data processing

### 📊 **Expected Performance:**
- **First query**: 3-5 seconds (normal cold start)
- **Subsequent queries**: 1-2 seconds (with caching)
- **Overall improvement**: 3-5x faster response times

### 🧪 **Testing Performance:**
```bash
# Compare original vs optimized versions
python test_performance.py

# Run optimized version
./ops_run_optimized_dev.sh  # or _prod.sh
```

---

## 🌐 Deployment to Streamlit Community Cloud

PAGie can be deployed for free on [Streamlit Community Cloud](https://streamlit.io/cloud):

### **Prerequisites:**
1. GitHub account with this repository pushed
2. Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### **Deployment Steps:**

#### 1. **Prepare Your Repository** (Already Done! ✅)
- `.streamlit/config.toml` - UI configuration
- `.streamlit/secrets.toml.example` - Secrets template
- Code updated to support Streamlit secrets

#### 2. **Deploy to Streamlit Cloud**
1. Visit: https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click **"New app"**
4. Configure:
   - **Repository:** `LK-Hour/PAGie`
   - **Branch:** `main`
   - **Main file:** `app.py`
5. Click **"Advanced settings"**

#### 3. **Add Your Secrets**
In the **Secrets** section, add:
```toml
GOOGLE_API_KEY = "your-actual-gemini-api-key-here"
```

#### 4. **Deploy!**
Click **"Deploy"** and wait 2-3 minutes for your app to go live! 🚀

### **Important Notes:**
- ⚠️ **Google Drive sync won't work in cloud** (requires OAuth tokens)
- ⚠️ **ChromaDB resets on each deployment** (not persistent in free tier)
- ✅ **Chat interface works perfectly** for demo purposes
- ✅ **Query existing ChromaDB** if you upload your `chroma_db/` to the repo

### **For Production Use:**
Consider upgrading to persistent storage:
- Use Google Cloud Storage for ChromaDB
- Implement proper OAuth flow for Google Drive
- Or use Streamlit's [file uploader](https://docs.streamlit.io/library/api-reference/widgets/st.file_uploader) for CV files

---

## 📂 Repository Structure
```text
PAGie_Project/
│
├── .github/
│   └── copilot-instructions.md   # System instructions for AI coding assistance
├── data/                         # Temporary storage for raw downloaded CV files
├── chroma_db/                    # Local Vector Database storage
│
├── sync_data.py                  # ETL Pipeline: Fetches CV files from specific Drive folder
├── data_science_eda.py           # Analyzes text chunks, applies IQR, generates graphs
├── rag_pipeline.py               # Core LangChain logic (Embeddings, ChromaDB, Gemini)
├── app.py                        # Streamlit Frontend Chatbot
│
├── requirements.txt              # Project dependencies
├── .env                          # Secure API Keys (Ignored by Git)
│
├── app_optimized.py              # ⚡ High-Performance Streamlit UI
├── rag_pipeline_optimized.py     # ⚡ High-Performance RAG Pipeline  
├── test_performance.py           # Performance testing & benchmarking
├── cache/                        # Embedding cache for faster queries
│
└── README.md                     # Project Documentation
