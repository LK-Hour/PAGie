# 🧠 PAGie: Personal AI Generation & Information Engine

**An Automated "Second Brain" RAG Pipeline using Google Drive, Notion, and Gemini 3.0**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-green)
![Gemini](https://img.shields.io/badge/Google_Gemini-3.0-orange)
![Data_Science](https://img.shields.io/badge/Data_Science-EDA_%26_IQR-purple)

## 📖 Project Overview
**PAGie** is a contextual AI assistant developed for an academic Data Science & Software Engineering project at CADT. It solves the problem of scattered personal knowledge by automatically ingesting unstructured data from **Google Drive** and **Notion**, applying rigorous Data Science cleaning techniques, and using **Retrieval-Augmented Generation (RAG)** to answer user queries with high precision.

### ✨ Key Features
* **Multi-Source ETL Pipeline:** Automatically fetches PDFs, Docs, and notes from Google Drive and Notion APIs.
* **Data Science Preprocessing:** Applies **Exploratory Data Analysis (EDA)** and the **Interquartile Range (IQR)** statistical method to detect and remove extreme text-chunk outliers, ensuring highly optimized LLM context.
* **Advanced RAG Architecture:** Utilizes Google's Text-Embedding models and **ChromaDB** for rapid vector similarity search.
* **Gemini 3.0 Integration:** Leverages Google's native multimodal LLM for accurate, hallucination-free answer generation.
* **Automated Nightly Sync:** Runs a scheduled CRON job to keep the knowledge base up to date without manual intervention.
* **Streamlit UI:** A clean, intuitive chat interface.

---

## 🛠️ Technology Stack
* **Language:** Python
* **Orchestration:** LangChain
* **LLM (Prod):** Google AI Studio (Gemini)
* **LLM (Dev):** Local Ollama model (`qwen3.5:2b`)
* **Embeddings:** Local Sentence-Transformers (`all-MiniLM-L6-v2`)
* **Vector Database:** ChromaDB
* **Data Extraction:** Google Drive API, Notion API
* **Data Science:** Pandas, NumPy, Matplotlib, Seaborn
* **Frontend UI:** Streamlit

---

## 🚀 Runtime Modes (Dev vs Prod)

PAGie supports two runtime modes via `.env`:

- `APP_MODE=dev` → Local LLM via Ollama (no Gemini rate-limit interruptions during development)
- `APP_MODE=prod` → Gemini (for final demo/report alignment with project proposal)

### Dev (local LLM)
```bash
./ops_run_dev_local.sh
```

### Prod (Gemini)
```bash
./ops_run_prod_gemini.sh
```

### Backup + Reset noisy DB + Rebuild vectors
```bash
./ops_backup_reset_rebuild.sh
```

---

## 📂 Repository Structure
```text
PAGie_Project/
│
├── .github/
│   └── copilot-instructions.md   # System instructions for AI coding assistance
├── data/                         # Temporary storage for raw downloaded files
├── chroma_db/                    # Local Vector Database storage
│
├── sync_data.py                  # ETL Pipeline: Fetches data from Drive & Notion
├── data_science_eda.py           # Analyzes text chunks, applies IQR, generates graphs
├── rag_pipeline.py               # Core LangChain logic (Embeddings, ChromaDB, Gemini)
├── app.py                        # Streamlit Frontend Chatbot
│
├── requirements.txt              # Project dependencies
├── .env                          # Secure API Keys (Ignored by Git)
└── README.md                     # Project Master Plan# PAGie
# PAGie
