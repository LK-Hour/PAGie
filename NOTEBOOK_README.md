# 📓 PAGie Jupyter Notebook - Academic Submission Guide

## 📋 Overview

This document explains how to use `PAGie_Complete_Pipeline.ipynb` - a comprehensive Jupyter notebook that demonstrates the complete RAG (Retrieval-Augmented Generation) pipeline for CV analysis.

**Intended Audience:** Professor/Teacher reviewing the Data Science project  
**Purpose:** Academic demonstration of the complete pipeline (excluding UI)

---

## 🎯 What's Included

The notebook covers the **entire PAGie pipeline** in 15 interactive steps:

### 📚 Learning Objectives Demonstrated:

1. **Software Engineering:**
   - Modular code architecture
   - API integration (Google Drive, Gemini)
   - Error handling and validation
   - Environment configuration

2. **Data Science:**
   - Exploratory Data Analysis (EDA)
   - Pandas DataFrame manipulation
   - Statistical visualization (Matplotlib, Seaborn)
   - Data quality assessment
   - Semantic filtering approach

3. **Artificial Intelligence:**
   - Vector embeddings (Sentence-Transformers)
   - Semantic search (ChromaDB)
   - Retrieval-Augmented Generation (RAG)
   - LLM integration (Google Gemini 3.0)

---

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Python 3.10+ installed
python --version

# 2. Install Jupyter
pip install jupyter notebook

# 3. Install project dependencies
cd "pagie_project"
pip install -r requirements.txt
```

### Running the Notebook

```bash
# Start Jupyter Notebook
jupyter notebook

# OR use JupyterLab (modern interface)
jupyter lab

# Navigate to: PAGie_Complete_Pipeline.ipynb
```

**Important:** You need a **Google API Key** for Gemini. Create a `.env` file:

```bash
# .env file
GOOGLE_API_KEY=your-api-key-here
```

Get your API key from: https://aistudio.google.com/app/apikey

---

## 📂 Project Structure

```
pagie_project/
├── PAGie_Complete_Pipeline.ipynb    ← 👈 THE MAIN NOTEBOOK
├── NOTEBOOK_README.md              ← This file
├── data/
│   └── drive/                      ← CV PDF files (3 CVs)
│       ├── KIMHOUR_LOEM_CV.pdf
│       ├── Luy_Virak_CV.pdf
│       └── LY_KIMKHENG_CV.pdf
├── assets/                         ← Generated visualizations
├── chroma_db/                      ← Vector database (auto-created)
├── requirements.txt                ← Python dependencies
└── .env                            ← API keys (create this)
```

---

## 📖 Notebook Sections

The notebook is divided into **15 progressive sections**:

| Section | Title | What It Does |
|---------|-------|--------------|
| 1 | Setup & Dependencies | Install packages, import libraries |
| 2 | Configuration | Set parameters (chunk size, model names, paths) |
| 3 | Load CV Documents | Use LangChain to load PDF files |
| 4 | Text Chunking | Split documents into 500-char chunks |
| 5 | Data Science Analysis | Create Pandas DataFrame for EDA |
| 6 | Data Visualization | Generate 4-panel EDA plots |
| 7 | Data Cleaning | Apply MIN_WORD_COUNT threshold filter |
| 8 | Vector Embeddings | Initialize Sentence-Transformers model |
| 9 | Build ChromaDB | Create vector database with 384-dim embeddings |
| 10 | Test Semantic Search | Validate retrieval with sample queries |
| 11 | Initialize Gemini LLM | Set up Google Gemini 3.0 Flash |
| 12 | Build RAG Pipeline | Combine retrieval + generation |
| 13 | Test Complete RAG | Run end-to-end tests with 5 sample questions |
| 14 | Interactive Query | Ask your own questions (optional) |
| 15 | Summary & Metrics | Final statistics and performance report |

---

## 🔑 Key Code Highlights

### Data Science - Statistical Analysis
```python
# Section 5: Build DataFrame
df_chunks = build_dataframe(raw_chunks)
print(df_chunks[['word_count', 'char_count']].describe())
```

### Data Visualization - 4-Panel EDA
```python
# Section 6: Generate comprehensive plots
# - Histogram (word count distribution)
# - Box plot (outlier detection)  
# - Bar chart (chunks per CV)
# - Statistics table (mean, median, IQR)
```

### Semantic Filtering (Not IQR)
```python
# Section 7: Simple threshold approach
df_clean = df[df['word_count'] >= MIN_WORD_COUNT]
# Note: IQR would be added for datasets with 1000+ chunks
```

### RAG Pipeline - Retrieval + Generation
```python
# Section 12: Complete pipeline
def query_pagie_rag(question, vectordb, llm, k=8):
    # 1. Retrieve top-k chunks via semantic search
    # 2. Build context from retrieved chunks
    # 3. Generate answer with Gemini LLM
    # 4. Return answer + sources + metadata
```

---

## 🧪 Expected Outputs

### Cell Execution Results:

1. **Section 3:** 
   ```
   ✅ Loaded 3 pages from CV files
   ```

2. **Section 4:**
   ```
   ✅ Created 16 chunks
   ```

3. **Section 6:**
   - Visual output: 4-panel EDA plot
   - Saved to: `assets/eda_report_notebook.png`

4. **Section 9:**
   ```
   ✅ Vector database created successfully!
   Total vectors: 16
   Database size: 512.0 KB
   ```

5. **Section 13:**
   - 5 test questions with complete answers
   - Response time: ~3-4 seconds per query

---

## 📊 Data Science Highlights

### Statistical Methods Used:

1. **Pandas DataFrame Analysis:**
   - `df.describe()` for statistical summary
   - `df['column'].mean()`, `.median()`, `.std()`
   - Grouping and aggregation

2. **Visualization Techniques:**
   - Histogram with mean/median lines
   - Box plot with IQR annotations
   - Bar chart with value labels
   - Table display with formatting

3. **Data Quality Metrics:**
   - Word count distribution
   - Character count analysis
   - Outlier detection (IQR method explained)
   - Filter effectiveness measurement

4. **Filtering Approach:**
   - **Current:** Semantic threshold (`MIN_WORD_COUNT = 5`)
   - **Explained:** Why IQR is better for larger datasets
   - **Honest:** Acknowledges proof-of-concept scale

---

## 🎓 Teaching Points

### What Professors Will Look For:

✅ **Understanding of Theory:**
- Can you explain why 500 characters for chunk size?
- Why use semantic search instead of keyword search?
- What is the difference between embeddings and LLM?

✅ **Code Quality:**
- Modular functions with docstrings
- Clear variable names
- Error handling
- Comments explaining "why" not just "what"

✅ **Data Science Rigor:**
- Proper use of Pandas for analysis
- Statistical visualization best practices
- Honest discussion of filtering method
- Understanding when to use IQR vs. thresholds

✅ **Critical Thinking:**
- Acknowledging limitations (small dataset)
- Explaining trade-offs (simple filter vs. IQR)
- Discussing future improvements
- Realistic scope assessment

---

## 🐛 Troubleshooting

### Common Issues:

**1. `GOOGLE_API_KEY` not found:**
```bash
# Create .env file in project root:
echo "GOOGLE_API_KEY=your-key-here" > .env
```

**2. ChromaDB database already exists:**
```python
# Section 9: Set reset=True to rebuild
vectordb = build_vector_database(clean_chunks, embeddings, reset=True)
```

**3. No CV files found:**
```bash
# Check directory structure
ls -la data/drive/
# Should show 3 PDF files
```

**4. Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

**5. Kernel crashes during embedding:**
```python
# Reduce batch size or restart kernel:
# Kernel → Restart & Clear Output
```

---

## 📝 Presentation Tips

### When Demonstrating to Professor:

1. **Start from Section 1:** Show the setup process

2. **Highlight Section 6:** The EDA visualization is the "wow" moment

3. **Explain Section 7:** Be honest about filtering approach
   - "For this proof-of-concept with 16 chunks, a simple threshold works well"
   - "For production with 1000+ chunks, I would implement IQR filtering"

4. **Demo Section 13:** Run the test queries live
   - Show how semantic search works
   - Point out the source attribution
   - Explain response time (3-4 seconds)

5. **Be Ready to Modify:** Professors love seeing you code live
   - "Can you try a different question?"
   - "What if we change k to 5 instead of 8?"
   - "Show me the raw DataFrame"

---

## 🎯 Evaluation Criteria

This notebook demonstrates:

| Criteria | How It's Shown | Section |
|----------|----------------|---------|
| **Data Loading** | LangChain DirectoryLoader for PDFs | 3 |
| **Data Processing** | RecursiveCharacterTextSplitter | 4 |
| **Statistical Analysis** | Pandas DataFrame with `.describe()` | 5 |
| **Visualization** | 4-panel Matplotlib/Seaborn plots | 6 |
| **Data Cleaning** | Threshold-based filtering | 7 |
| **Machine Learning** | Sentence-Transformers embeddings | 8 |
| **Vector Database** | ChromaDB implementation | 9 |
| **Information Retrieval** | Semantic search testing | 10 |
| **LLM Integration** | Google Gemini API | 11 |
| **RAG Architecture** | Complete pipeline function | 12 |
| **Testing** | 5 realistic test cases | 13 |
| **Documentation** | Markdown cells + docstrings | All |

---

## 🚀 Advanced Usage

### Custom Queries:

```python
# Section 14: Interactive mode
interactive_query()

# Or single query:
result = query_pagie_rag("Find Python developers", vectordb, llm)
print(result['answer'])
```

### Experiment with Parameters:

```python
# Change chunk size:
CHUNK_SIZE = 1000  # Larger chunks
CHUNK_OVERLAP = 100

# Change retrieval count:
RETRIEVAL_K = 5  # Retrieve fewer chunks

# Re-run from Section 4 onwards
```

### Export Results:

```python
# Save answers to file
with open('results.txt', 'w') as f:
    for question in test_questions:
        result = query_pagie_rag(question, vectordb, llm)
        f.write(f"Q: {question}\n")
        f.write(f"A: {result['answer']}\n\n")
```

---

## 📚 Further Reading

**LangChain Documentation:**
- https://python.langchain.com/docs/

**Sentence-Transformers:**
- https://www.sbert.net/

**ChromaDB:**
- https://docs.trychroma.com/

**Google Gemini API:**
- https://ai.google.dev/gemini-api/docs

**RAG Fundamentals:**
- https://docs.llamaindex.ai/en/stable/getting_started/concepts/

---

## ✅ Submission Checklist

Before sharing with professor:

- [ ] Notebook runs without errors (Kernel → Restart & Run All)
- [ ] All visualizations display correctly
- [ ] API key is set in `.env` (not hardcoded!)
- [ ] Output cells show expected results
- [ ] CV files are present in `data/drive/`
- [ ] `requirements.txt` is up to date
- [ ] This README is included
- [ ] Git repository is clean (no sensitive data)

---

## 📧 Support

If you have questions about the notebook:

1. Check the inline markdown documentation
2. Review the docstrings in each function
3. Run cells sequentially (don't skip sections)
4. Check troubleshooting section above

---

**Good luck with your presentation! 🎓✨**

---

*This notebook was created for academic purposes as part of the Data Science course (Y3 T2) at CADT, Cambodia. It demonstrates the complete implementation of a Retrieval-Augmented Generation system for CV analysis.*
