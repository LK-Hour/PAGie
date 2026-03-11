


This is an incredible idea. If you want GitHub Copilot to truly understand your vision, and if you want to impress anyone who looks at your repository (like a professor or future employer), you need a **Master `README.md` file**.

A great `README.md` acts as the homepage of your project. It explains the "Why", the "How", and tracks the progress using GitHub task checkboxes. 

Create a file named `README.md` in the root of your folder, and paste this entire block of Markdown code into it. Copilot will read this file to understand the entire architecture!

***

```markdown
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
* **LLM & Embeddings:** Google AI Studio (Gemini 3.0 / Flash)
* **Vector Database:** ChromaDB
* **Data Extraction:** Google Drive API, Notion API
* **Data Science:** Pandas, NumPy, Matplotlib, Seaborn
* **Frontend UI:** Streamlit

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
└── README.md                     # Project Master Plan
```

---

## 🗺️ Implementation Roadmap (Project Plan)

### Phase 1: Environment & Setup 
- [x] Define project name and architecture (PAGie).
-[x] Set up Python Virtual Environment (`venv`).
- [x] Create `.github/copilot-instructions.md`.
- [ ] Install dependencies (`langchain`, `streamlit`, `pandas`, `chromadb`, etc.).
- [ ] Securely configure `.env` with Google API and Notion API keys.

### Phase 2: Data Ingestion (ETL - Extract)
- [ ] Implement `GoogleDriveLoader` to fetch files from the dedicated `PAGie_Knowledge_Base` folder.
- [ ] Implement `NotionDirectoryLoader` to fetch academic task boards and notes.
- [ ] Combine data sources into a unified LangChain document structure.

### Phase 3: Data Science & Preprocessing (EDA & IQR)
- [ ] Split documents into manageable text chunks using `RecursiveCharacterTextSplitter`.
- [ ] Convert chunk metadata into a Pandas DataFrame.
- [ ] **Data Science Requirement:** Calculate Q1, Q3, and IQR for chunk word counts.
- [ ] Filter out statistical outliers (chunks that are too small or massive unreadable blocks).
- [ ] Generate EDA visualizations (Histograms, Boxplots) using Matplotlib/Seaborn and save to `/assets`.

### Phase 4: Vector Storage (ETL - Load)
- [ ] Initialize `GoogleGenerativeAIEmbeddings`.
- [ ] Set up local `ChromaDB` instance.
- [ ] Embed the cleaned, IQR-filtered text chunks and persist them to the database.

### Phase 5: The AI Brain (Gemini 3.0 RAG)
- [ ] Initialize `ChatGoogleGenerativeAI` (Gemini 3.0).
- [ ] Build the retrieval chain (User Query -> Vector Search -> Context Injection -> LLM).
- [ ] Engineer the system prompt to give PAGie its persona and strict accuracy rules.

### Phase 6: User Interface & Automation
- [ ] Develop `app.py` using Streamlit for a ChatGPT-like interface.
- [ ] Add a sidebar displaying database metrics (e.g., Total Docs, Last Sync Time).
-[ ] Implement `schedule` in `sync_data.py` to run the ETL process automatically every night.

### Phase 7: Evaluation & Final Polish
- [ ] Create a Ground Truth test set of 50 questions based on personal documents.
- [ ] Evaluate Retrieval Hit Rate (>90% target).
- [ ] Evaluate Generation Hallucination Rate (<5% target).
- [ ] Prepare final presentation slides and PDF report for grading.
```

***

### How this helps you:
1. **GitHub Copilot reads this:** When you open a file, Copilot scans your `README.md`. Because the Roadmap is laid out perfectly, it knows exactly what part of the project you are currently coding.
2. **You stay organized:** You can literally tick the checkboxes `- [x]` as we finish each step! 
3. **Professor points:** If your professor looks at your GitHub repo, seeing a structured `README.md` with badging, directory trees, and checked-off tasks is an instant A+ in software engineering practices.

**Are you ready to check off the rest of Phase 1 by creating your `.env` file and getting that Google API key?**