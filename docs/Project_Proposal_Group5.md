  
Faculty of Digital Engineering  
Department of Computer Science  
Specialized in Software Engineering

# 

Group 5:  
Student name: Kimhour Loem, Virak Luy, Kimkheng Ly,Sovicheakta Penh, Sakura Te

# **Project Proposal: Personal AI Assistant**

An Automated RAG Pipeline using Google Drive, Notion, and Gemini 3.0

### **1\. Introduction**

* **Context of the problem:** In the modern academic environment, students generate massive amounts of unstructured digital data scattered across multiple platforms, primarily Google Drive (PDFs, slides, documents) and Notion (notes, task trackers, databases).

* **Why the problem is important:** Manually searching through folders and workspaces to find specific information, deadlines, or study notes is highly inefficient and time-consuming.

* **Brief explanation of the dataset and analysis:** This project analyzes a proprietary dataset of personal academic documents extracted via the Google Drive and Notion APIs. By applying Natural Language Processing (NLP) and Data Science techniques (EDA, IQR filtering), the project will build an automated Retrieval-Augmented Generation (RAG) pipeline to power a contextual AI assistant capable of answering questions based on the student's personal data.

### **2\. Problem Statement**

* How can we efficiently extract, clean, and retrieve accurate information from scattered, unstructured personal data across Google Drive and Notion?

* Can we build an automated, nightly ETL (Extract, Transform, Load) pipeline that keeps the AI’s knowledge base constantly updated without manual user input?

### **3\. Project Objective**

* Automatically extract and ingest unstructured text data using the Google Drive and Notion APIs.

* Clean and preprocess the text data using statistical outlier detection (IQR) to optimize AI token context.

* Perform Exploratory Data Analysis (EDA) on document metadata and text chunk characteristics.

* Develop a high-accuracy RAG model using Google's Gemini 3.0 and a local Vector Database (ChromaDB).

* Deploy a user-friendly chatbot interface (via Streamlit) with a response latency of under 5 seconds.

### **4\. Dataset Description**

* **Dataset source:** Proprietary personal data accessed dynamically via the standard Google Drive API and Notion Integration API.

* **Number of records:** Estimated 500+ unstructured documents (PDFs, DOCX, TXT) and Notion pages.

* **Number of features:** Extracted metadata includes Source\_Platform (Drive vs. Notion), File\_Type, Creation\_Date, Token\_Count, and Raw\_Text.


### **5\. Data Preprocessing / Data Cleaning**

Since RAG systems require clean text chunks, data preparation is a critical step:

* **Handling Missing Values:** Dropping corrupted files or Notion pages that contain zero text content.

* **Text Normalization:** Using Gemini 3.0’s multimodal capabilities to extract clean text from messy PDFs, bypassing traditional, error-prone OCR.

* **Chunking & IQR Outlier Removal:** Large documents will be split into smaller blocks (e.g., 500 words). We will calculate the token count of every chunk and apply the **Interquartile Range (IQR)** statistical method. Chunks that are extreme outliers on the low end (e.g., 5 words, providing no context) or the high end (e.g., massive unbroken text walls) will be removed to ensure high-quality training data for the AI.


### **6\. EDA (Exploratory Data Analysis)**

To understand the distribution of the personal knowledge base, the following visualizations will be generated using Pandas, Matplotlib, and Seaborn:

* **Pie Chart:** Percentage of total knowledge stored in Notion vs. Google Drive.

* **Histogram:** Distribution of chunk token lengths across the entire dataset.

* **Boxplot:** Comparing the average word count of Google Drive files versus Notion pages.

* **Expected Insight:** We expect the EDA to reveal that Notion pages consist of shorter, highly structured bullet points, while Google Drive documents contain longer, denser paragraphs, requiring adaptive chunking strategies.

### **7\. Proposed Methodology & Modeling**

To achieve the project objectives, we will implement a technical approach utilizing a modern AI and Data Science technology stack.

* **Model Type:**

  * *Embedding Model:* Google Text-Embedding (converts text to vector numbers).

  * *Vector Database:* ChromaDB (stores the embeddings).

  * *Generator Model:* Gemini 3.0 via Google AI Studio (generates the final answer).

* **Why the model was chosen:** Gemini 3.0 is selected for its seamless integration with Google ecosystem data, its massive context window, and its native multimodal ability to "read" complex PDFs without extra OCR libraries.

* **Training/Implementation Process:** A CRON job will run nightly to fetch new documents, process them through the IQR cleaning script, generate embeddings, and index them into ChromaDB.

* **Train/Test Split:** Since this is an unsupervised RAG pipeline, the "Test Set" will consist of a manually created Ground Truth dataset of 50 custom Q\&A pairs based on the personal documents (e.g., *"When is my Data Science proposal due according to Notion?"*).

**Technology Stack:**

* Data Extraction: Google Drive API, Notion API, CRON (for nightly scheduling).

* Data Processing & EDA: Python, Pandas, NumPy, Matplotlib, Seaborn.

* AI & Machine Learning: LangChain, Google Gemini 3.0 (via Google AI Studio), Google Text-Embedding.

* Database & Deployment: ChromaDB (Vector Database), Streamlit (Web UI).

**Workflow Pipeline:**

1. Data Collection: CRON job triggers the APIs to securely download new/modified files from Drive and Notion.

2. Preprocessing: Text is extracted, normalized, and split into chunks. The IQR method removes statistical outliers.

3. Embedding: Clean chunks are passed to the Google Embedding model to convert text semantics into vector numbers.

4. Vector Storage: Embeddings are indexed and stored locally in ChromaDB.

5. Retrieval: When a user asks a question, the system queries ChromaDB using Cosine Similarity to find the most relevant document chunks.

6. Generation: The retrieved chunks are fed into Gemini 3.0 to synthesize a highly accurate, context-aware answer.

   

### **8\. Result and Evaluation**

The model's performance will be evaluated using specialized RAG retrieval metrics rather than traditional classification metrics:

* **Retrieval Hit Rate:** The percentage of times the system successfully retrieves the correct source document from the top 3 vector matches (Target: \>90%).

* **Generation Accuracy:** Measuring whether Gemini 3.0 answered the prompt correctly based *only* on the provided context (Target: \<5% hallucination rate).

* **Execution Latency:** Time taken from user prompt to complete answer generation (Target: \<5 seconds).

3
### **9\. Discussion / Conclusion**

**1\. Discussion:** We will analyze which features (metadata vs. raw text) were most important for the AI's retrieval success. Insights will include how combining different API sources (Notion \+ Drive) impacted the AI's ability to cross-reference personal data.

**2\. Conclusion:** The final report will summarize whether the automated nightly ETL pipeline was successfully established, if the IQR cleaning improved AI performance, and whether the primary objective of creating a reliable, highly accurate "Second Brain" chatbot was achieved.