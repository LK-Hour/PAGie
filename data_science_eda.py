"""
data_science_eda.py — Data Science Processing Pipeline for PAGie (CV-Focused)
==============================================================================
This is the core Data Science module for CV analysis. It implements the full
preprocessing and analysis pipeline as specified in the project proposal:

  1. LOAD     → Load all CV files from ./data/drive/ (Google Drive folder)
  2. CHUNK    → Split CV documents into fixed-size text chunks
  3. ANALYZE  → Convert chunks to a Pandas DataFrame with word-count statistics
  4. FILTER   → Apply minimum word-count threshold to remove empty/invalid chunks
  5. VISUALIZE → Generate 4 EDA plots and save to ./assets/eda_report.png
  6. EMBED    → Vectorize clean chunks and persist them to ChromaDB

Usage:
  python data_science_eda.py
"""

import json
import logging
import os
import re
import shutil
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# OCR imports for image-based PDFs - optional for cloud deployment
try:
    import pytesseract
    from pdf2image import convert_from_path
    _ocr_available = True
except ImportError:
    _ocr_available = False
    pytesseract = None
    convert_from_path = None

from PIL import Image

# Load API keys from .env — required for embedding model.
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path("./data")

# Use writable directories on Streamlit Cloud
# FORCE_LOCAL_MODE=true forces local paths even when Streamlit is detected
FORCE_LOCAL_MODE = os.getenv("FORCE_LOCAL_MODE", "false").lower() == "true"

if FORCE_LOCAL_MODE:
    # Force local paths (for app_local.py)
    ASSETS_DIR = Path("./assets")
    CHROMA_DB_DIR = "./chroma_db"
else:
    # Auto-detect environment
    try:
        import streamlit as st
        if os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("STREAMLIT_CLOUD") == "true":
            # On Streamlit Cloud, use /tmp (writable)
            ASSETS_DIR = Path("/tmp/assets")
            CHROMA_DB_DIR = "/tmp/chroma_db"
        else:
            ASSETS_DIR = Path("./assets")
            CHROMA_DB_DIR = "./chroma_db"
    except (ImportError, AttributeError):
        ASSETS_DIR = Path("./assets")
        CHROMA_DB_DIR = "./chroma_db"

# Optional ingestion hygiene controls (comma-separated globs / regex-lite substrings)
EXCLUDE_SOURCE_PATTERNS = [p.strip().lower() for p in os.getenv("EXCLUDE_SOURCE_PATTERNS", "").split(",") if p.strip()]
INCLUDE_ONLY_SOURCE_PATTERNS = [p.strip().lower() for p in os.getenv("INCLUDE_ONLY_SOURCE_PATTERNS", "").split(",") if p.strip()]
MIN_CHARS_PER_DOC = int(os.getenv("MIN_CHARS_PER_DOC", "40"))
RESET_CHROMA_ON_REBUILD = os.getenv("RESET_CHROMA_ON_REBUILD", "true").lower() == "true"

# Chunk size in characters — 500 chars ≈ 80-100 words, a good RAG context unit.
# Overlap ensures that context spanning chunk boundaries is not lost.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# File that saves embedding progress so the pipeline can resume after
# a daily quota reset without re-embedding already processed batches.
CHECKPOINT_FILE = DATA_DIR / "embed_checkpoint.json"

# Local sentence-transformers model used for embeddings.
# Runs entirely on CPU — no API key, no quota, no cost.
# all-MiniLM-L6-v2: 80 MB model, 384-dim vectors, excellent for RAG retrieval.
# Downloaded automatically on first run and cached in ~/.cache/huggingface/
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Ensure output directories exist (especially important for /tmp on Streamlit Cloud)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
Path(CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text Cleaning Functions for CV Processing
# ---------------------------------------------------------------------------
def clean_ocr_text(text: str) -> str:
    """
    Clean OCR-extracted text to remove excessive spacing and formatting artifacts.
    
    Args:
        text: Raw OCR text with potential spacing issues
        
    Returns:
        Cleaned text with proper spacing and formatting
    """
    if not text:
        return text
    
    # Remove excessive spacing between individual characters
    # Pattern: "H  e  l  l  o" -> "Hello"
    text = re.sub(r'\b([A-Za-z])\s+([A-Za-z])\s+([A-Za-z])', r'\1\2\3', text)
    text = re.sub(r'\b([A-Za-z])\s+([A-Za-z])', r'\1\2', text)
    
    # Fix common OCR character spacing patterns
    text = re.sub(r'(\w)\s+(\w)\s+(\w)\s+(\w)', r'\1\2\3\4', text)  # 4-letter words
    text = re.sub(r'(\w)\s+(\w)\s+(\w)', r'\1\2\3', text)          # 3-letter words  
    
    # Multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR mistakes
    text = text.replace('|', 'I')  # Pipe to I
    text = text.replace('0', 'O')  # Zero to O in names (context-dependent)
    
    # Clean up line breaks and extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
    text = text.strip()
    
    return text

def clean_cv_text_content(text: str) -> str:
    """
    Specialized cleaning for CV/Resume text content.
    
    Args:
        text: CV text content
        
    Returns:
        Cleaned CV text optimized for RAG retrieval
    """
    if not text:
        return text
    
    # First apply OCR cleaning
    text = clean_ocr_text(text)
    
    # CV-specific cleaning patterns
    # Remove email artifacts from OCR
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', lambda m: m.group().replace(' ', ''), text)
    
    # Fix phone numbers with spaces
    text = re.sub(r'(\+?\d)\s+(\d)\s+(\d)', r'\1\2\3', text)
    
    # Standardize section headers (remove extra spacing)
    cv_sections = ['EDUCATION', 'EXPERIENCE', 'SKILLS', 'PROJECTS', 'CONTACT', 'SUMMARY', 'OBJECTIVE']
    for section in cv_sections:
        spaced_section = ' '.join(section)  # "E D U C A T I O N"
        text = text.replace(spaced_section, section)
    
    # Remove excessive punctuation
    text = re.sub(r'[•]{2,}', '•', text)  # Multiple bullets to single
    text = re.sub(r'[-]{3,}', '---', text)  # Multiple dashes to triple
    
    return text


# ===========================================================================
# STEP 1 — LOAD: Read all raw documents from ./data/
# ===========================================================================

def _should_keep_source(source: str) -> bool:
    s = source.lower()

    if INCLUDE_ONLY_SOURCE_PATTERNS:
        if not any(token in s for token in INCLUDE_ONLY_SOURCE_PATTERNS):
            return False

    if EXCLUDE_SOURCE_PATTERNS and any(token in s for token in EXCLUDE_SOURCE_PATTERNS):
        return False

    return True


def load_pdf_with_ocr(pdf_path: Path) -> list:
    """
    Load PDF with OCR fallback for image-based documents.
    
    First attempts standard text extraction using PyPDFLoader.
    If no text is found, uses OCR (Tesseract) to extract text from PDF images.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of LangChain Document objects with extracted text
    """
    documents = []
    
    try:
        # Step 1: Try standard PDF text extraction
        loader = PyPDFLoader(str(pdf_path))
        pdf_docs = loader.load()
        
        # Clean the extracted text from standard PDF
        for doc in pdf_docs:
            if doc.page_content:
                doc.page_content = clean_cv_text_content(doc.page_content)
        
        # Check if any meaningful text was extracted after cleaning
        total_text_length = sum(len((doc.page_content or "").strip()) for doc in pdf_docs)
        
        if total_text_length > 50:  # Require meaningful content length
            logger.info(f"  📄 Standard text extraction successful: {pdf_path.name}")
            return pdf_docs
        else:
            logger.info(f"  🖼️  Insufficient text found in {pdf_path.name}, attempting OCR...")
            
            # Check if OCR is available
            if not _ocr_available:
                logger.warning(f"  ⚠️  OCR not available (pytesseract/pdf2image not installed). Skipping {pdf_path.name}")
                return pdf_docs  # Return what we have, even if minimal
            
            # Step 2: Use OCR for image-based PDFs
            try:
                # Convert PDF pages to images
                images = convert_from_path(str(pdf_path), dpi=200)
                
                for page_num, image in enumerate(images, 1):
                    # Extract text using Tesseract OCR
                    ocr_text = pytesseract.image_to_string(image, lang='eng')
                    
                    # Clean the OCR text to remove spacing artifacts
                    cleaned_text = clean_cv_text_content(ocr_text)
                    
                    if cleaned_text.strip():
                        # Create a Document object similar to PyPDFLoader format
                        doc = Document(
                            page_content=cleaned_text,
                            metadata={
                                "source": str(pdf_path),
                                "page": page_num - 1,  # 0-indexed like PyPDFLoader
                                "extraction_method": "OCR_cleaned"
                            }
                        )
                        documents.append(doc)
                        logger.info(f"    📝 OCR extracted and cleaned {len(cleaned_text)} chars from page {page_num}")
                    else:
                        logger.warning(f"    ⚠️  No useful text found on page {page_num} after OCR cleaning")
                        
                if documents:
                    logger.info(f"  ✅ OCR extraction successful: {pdf_path.name} ({len(documents)} pages)")
                else:
                    logger.warning(f"  ❌ No text extracted via OCR: {pdf_path.name}")
                    
                return documents
                
            except Exception as ocr_error:
                logger.error(f"  ❌ OCR failed for {pdf_path.name}: {ocr_error}")
                return []
                
    except Exception as e:
        logger.error(f"  ❌ Failed to process PDF {pdf_path.name}: {e}")
        return []


def load_documents() -> list:
    """
    Loads only CV documents from the ./data/drive/ directory.

    This ensures PAGie focuses exclusively on CV/Resume analysis by only
    loading documents from the Google Drive CV folder, excluding any
    Notion or other data sources.

    Returns:
        A list of LangChain Document objects, each containing page_content
        and metadata (source path, platform).
    """
    all_docs = []

    # --- Load .txt files ONLY from the drive/ directory (CV-focused) ---
    drive_dir = DATA_DIR / "drive"
    if drive_dir.exists():
        try:
            txt_loader = DirectoryLoader(
                str(drive_dir),  # Only load from data/drive/, not entire data/
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
                silent_errors=True,  # Skip files with encoding errors gracefully.
            )
            txt_docs = txt_loader.load()

            # Attach source platform metadata and apply filters.
            kept_txt_docs = []
            for doc in txt_docs:
                source = doc.metadata.get("source", "")
                if not _should_keep_source(source):
                    continue
                if len((doc.page_content or "").strip()) < MIN_CHARS_PER_DOC:
                    continue
                doc.metadata["platform"] = "Google Drive CV"
                kept_txt_docs.append(doc)

            all_docs.extend(kept_txt_docs)
            logger.info(f"Loaded {len(kept_txt_docs)} CV text file(s) after filtering.")

        except Exception as e:
            logger.error(f"Error loading CV .txt files: {e}")
    else:
        logger.warning(f"CV directory {drive_dir} does not exist. Run sync_data.py first.")

    # --- Load .pdf files ONLY from the drive/ directory (CV-focused) ---
    if drive_dir.exists():
        try:
            pdf_paths = list(drive_dir.rglob("*.pdf"))  # Only scan drive/ directory
            for pdf_path in pdf_paths:
                try:
                    # Use OCR-enabled PDF loader
                    pdf_docs = load_pdf_with_ocr(pdf_path)
                    
                    kept_pdf_docs = []
                    for doc in pdf_docs:
                        source = doc.metadata.get("source", str(pdf_path))
                        if not _should_keep_source(source):
                            continue
                        if len((doc.page_content or "").strip()) < MIN_CHARS_PER_DOC:
                            continue
                        # Add extraction method to metadata
                        extraction_method = doc.metadata.get("extraction_method", "Standard")
                        doc.metadata["platform"] = f"Google Drive CV ({extraction_method})"
                        kept_pdf_docs.append(doc)
                        
                    if kept_pdf_docs:
                        all_docs.extend(kept_pdf_docs)
                        extraction_info = f"({kept_pdf_docs[0].metadata.get('extraction_method', 'Standard')})"
                        logger.info(f"  ✅ Loaded CV PDF: {pdf_path.name} {extraction_info} ({len(kept_pdf_docs)} page chunk(s))")
                    else:
                        logger.warning(f"  ⚠️  Filtered out {pdf_path.name} (no content after filtering)")
                        
                except Exception as e:
                    logger.error(f"  ❌ Failed to load CV PDF '{pdf_path.name}': {e}")

        except Exception as e:
            logger.error(f"Error scanning for CV PDF files: {e}")
    else:
        logger.warning(f"CV directory {drive_dir} does not exist for PDF loading.")

    logger.info(f"Total documents loaded: {len(all_docs)}")
    return all_docs


# ===========================================================================
# STEP 2 — CHUNK: Split documents into fixed-size text chunks
# ===========================================================================

def chunk_documents(documents: list) -> list:
    """
    Splits raw documents into smaller, overlapping text chunks.

    Why chunking? LLMs have finite context windows. Splitting documents into
    smaller units allows us to retrieve only the most relevant portions
    instead of dumping entire documents into the prompt.

    We use RecursiveCharacterTextSplitter which intelligently splits on
    paragraph breaks → newlines → spaces, preserving sentence integrity.

    Args:
        documents: List of LangChain Document objects.

    Returns:
        A flat list of smaller Document chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Split {len(documents)} document(s) into {len(chunks)} raw chunks.")
    return chunks


# ===========================================================================
# STEP 3 — ANALYZE: Build a Pandas DataFrame for statistical analysis
# ===========================================================================

def build_dataframe(chunks: list) -> pd.DataFrame:
    """
    Converts LangChain Document chunks into a structured Pandas DataFrame.

    Each row represents one text chunk with the following features:
      - chunk_id   : Integer index used to reference back to the chunks list.
      - word_count : Number of words (primary feature for IQR analysis).
      - char_count : Number of characters.
      - platform   : 'Google Drive' (all CV files come from Drive).
      - source     : Full file path of the originating CV document.

    Args:
        chunks: List of LangChain Document objects (raw chunks).

    Returns:
        A Pandas DataFrame with one row per chunk.
    """
    records = []
    for i, chunk in enumerate(chunks):
        word_count = len(chunk.page_content.split())
        records.append({
            "chunk_id": i,
            "text": chunk.page_content,
            "word_count": word_count,
            "char_count": len(chunk.page_content),
            "platform": chunk.metadata.get("platform", "Unknown"),
            "source": chunk.metadata.get("source", "Unknown"),
        })

    df = pd.DataFrame(records)
    logger.info(f"DataFrame created — Shape: {df.shape}")
    logger.info(f"\n--- Descriptive Statistics (before filtering) ---\n{df[['word_count', 'char_count']].describe().to_string()}")
    return df


# ===========================================================================
# STEP 4 — QUALITY FILTER: Remove semantically empty chunks
# ===========================================================================

# Minimum number of words a chunk must contain to be considered meaningful.
# Chunks below this threshold are typically parsing artifacts: page numbers,
# lone headers, watermarks, or stray characters — not real knowledge.
# No upper bound is applied: long chunks still carry valid, complete information
# and the embedding model handles them correctly within its token limit.
MIN_WORD_COUNT = 5


def apply_semantic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes semantically empty chunks using a minimum word-count threshold.

    For CV analysis, we want to preserve all meaningful content regardless of length.
    This filter only removes genuinely empty or invalid chunks (page numbers, 
    stray OCR characters, empty table cells) using a domain-appropriate threshold.

    Design rationale
    ----------------
    A simple word-count threshold (>= MIN_WORD_COUNT, default: 5) removes
    genuine artifacts without discarding valuable CV content:
      
      • Short chunks like "Python, Java, React" (skills) are preserved
      • Long chunks with detailed experience descriptions are preserved  
      • Only truly empty chunks (page numbers, OCR errors) are removed

    This approach is unbiased with respect to chunk length and preserves
    all semantically valuable CV information.

    Args:
        df: DataFrame with a 'word_count' column.

    Returns:
        A filtered DataFrame retaining all chunks with >= MIN_WORD_COUNT words.
    """
    logger.info("\n--- Chunk Quality Filter Analysis ---")
    logger.info(f"  Applied threshold     : word_count >= {MIN_WORD_COUNT} (semantic minimum)")
    
    # Apply the semantic minimum threshold — preserves all meaningful content.
    df_filtered = df[df["word_count"] >= MIN_WORD_COUNT].copy()

    removed = len(df) - len(df_filtered)
    logger.info(f"  Artifacts removed     : {removed} chunks ({removed / len(df) * 100:.1f}%)")
    logger.info(f"  Clean chunks retained : {len(df_filtered)} chunks")

    return df_filtered


# ===========================================================================
# STEP 5 — VISUALIZE: Generate EDA plots as per the project proposal
# ===========================================================================

def generate_eda_plots(df_raw: pd.DataFrame, df_filtered: pd.DataFrame):
    """
    Generates and saves a 2×2 panel of EDA visualizations to ./assets/eda_report.png.

    The four charts provide analysis of the CV dataset:

      [Top-Left]  Histogram  — CV chunk word count distribution, before vs. after quality filter.
                               Shows the applied minimum threshold and post-filter mean.

      [Top-Right] Boxplot    — Word count distribution for CV documents.
                               Shows consistency and spread of CV content chunks.

      [Bot-Left]  Pie Chart  — Proportion of total chunks by CV source files.
                               Shows data distribution across different CV documents.

      [Bot-Right] Scatter    — Quality filter map. Red × = removed artifacts (< 5 words).
                               Shows which chunks were filtered out as noise.

    Args:
        df_raw      : DataFrame before filtering (all chunks).
        df_filtered : DataFrame after filtering (clean chunks only).
    """
    sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "PAGie — CV Database Exploratory Data Analysis (EDA)",
        fontsize=17,
        fontweight="bold",
        y=1.01,
    )

    # -----------------------------------------------------------------------
    # Plot 1 (Top-Left): Histogram — Before vs. After quality filter
    # -----------------------------------------------------------------------
    ax1 = axes[0, 0]
    ax1.hist(df_raw["word_count"], bins=30, alpha=0.45, color="#4C72B0", label="Before filtering")
    ax1.hist(df_filtered["word_count"], bins=30, alpha=0.75, color="#55A868", label="After filtering")
    ax1.set_title("CV Chunk Word Count Distribution\n(Before vs. After Quality Filtering)")
    ax1.set_xlabel("Word Count per Chunk")
    ax1.set_ylabel("Number of Chunks")
    ax1.axvline(MIN_WORD_COUNT, color="orange", linestyle="--", linewidth=1.8,
                label=f"Min threshold ({MIN_WORD_COUNT} words)")
    ax1.axvline(df_filtered["word_count"].mean(), color="darkgreen", linestyle="--",
                linewidth=1.5, label=f'Mean after: {df_filtered["word_count"].mean():.0f} words')
    ax1.legend(fontsize=9)

    # -----------------------------------------------------------------------
    # Plot 2 (Top-Right): Boxplot — Word count distribution
    # -----------------------------------------------------------------------
    ax2 = axes[0, 1]
    ax2.boxplot(df_filtered["word_count"], patch_artist=True,
                boxprops={"facecolor": "#4C72B0", "alpha": 0.7},
                medianprops={"color": "black", "linewidth": 2})
    ax2.set_title("CV Content Word Count Distribution")
    ax2.set_xlabel("CV Dataset")
    ax2.set_ylabel("Word Count per Chunk")
    ax2.set_xticklabels(["All CVs"])

    # -----------------------------------------------------------------------
    # Plot 3 (Bot-Left): Pie Chart — CV file distribution
    # -----------------------------------------------------------------------
    ax3 = axes[1, 0]
    # Group by source file (CV name)
    source_counts = df_filtered.groupby("source").size().nlargest(8)  # Top 8 CV files
    colors_pie = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#CCB974", "#64B5CD", "#CA7EB8"][:len(source_counts)]
    
    # Shorten source paths to just filenames
    source_labels = [Path(s).name for s in source_counts.index]
    
    wedges, texts, autotexts = ax3.pie(
        source_counts,
        labels=source_labels,
        autopct="%1.1f%%",
        colors=colors_pie,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight("bold")
    ax3.set_title("CV Data Distribution\n(Top 8 Files by Chunk Count)")

    # -----------------------------------------------------------------------
    # Plot 4 (Bot-Right): Scatter — Chunk quality filter map
    # Shows which chunks were removed (below MIN_WORD_COUNT) vs. kept,
    # and overlays the IQR fences as reference lines to illustrate why
    # the data-driven IQR approach is not suitable here (lower fence is
    # negative, meaning it would never filter anything meaningful).
    # -----------------------------------------------------------------------
    ax4 = axes[1, 1]

    Q1 = df_raw["word_count"].quantile(0.25)
    Q3 = df_raw["word_count"].quantile(0.75)
    IQR_val = Q3 - Q1
    iqr_lower = Q1 - 1.5 * IQR_val
    iqr_upper = Q3 + 1.5 * IQR_val

    is_removed = df_raw["word_count"] < MIN_WORD_COUNT

    # Plot kept and removed chunks with distinct styles.
    ax4.scatter(
        df_raw.index[~is_removed],
        df_raw.loc[~is_removed, "word_count"],
        alpha=0.35, s=10, color="#55A868", label="Kept",
    )
    ax4.scatter(
        df_raw.index[is_removed],
        df_raw.loc[is_removed, "word_count"],
        alpha=0.9, s=35, color="#C44E52", label=f"Removed (< {MIN_WORD_COUNT} words)", marker="x",
    )
    # Applied threshold line.
    ax4.axhline(MIN_WORD_COUNT, color="red", linestyle="-", linewidth=2,
                label=f"Applied threshold ({MIN_WORD_COUNT} words)")
    ax4.set_title("CV Chunk Quality Filter Map\n(Retention vs. Removal)")
    ax4.set_xlabel("Chunk Index")
    ax4.set_ylabel("Word Count")
    ax4.legend(fontsize=8)

    plt.tight_layout()

    save_path = ASSETS_DIR / "eda_report.png"
    plt.savefig(str(save_path), dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"📊 EDA report saved → {save_path}")


# ===========================================================================
# STEP 6 — EMBED & STORE: Vectorize clean chunks → ChromaDB
# ===========================================================================

def embed_and_store(df_filtered: pd.DataFrame, all_chunks: list) -> Chroma:
    """
    Embeds quality-filtered text chunks using Google's embedding model
    and persists them to the local ChromaDB vector database.

    The embedding model converts each text chunk into a high-dimensional
    vector that represents its semantic meaning. ChromaDB stores these
    vectors so that at query time, cosine similarity can be used to find
    the chunks most relevant to the user's question.

    Rate-limit handling (Free Tier = 100 requests/minute):
      Chunks are processed in small batches with a short sleep between
      each batch so we never exceed the API quota. On a 429 error the
      function automatically waits and retries — no manual intervention needed.

    Only chunks that survived IQR filtering are embedded — this is the
    critical connection between the Data Science pipeline and the RAG pipeline.

    Args:
        df_filtered  : DataFrame of clean chunks (post-semantic-filtering), with chunk_id column.
        all_chunks   : The full list of LangChain Document chunks (pre-filter).

    Returns:
        The populated Chroma vector store object.

    Raises:
        Exception: If the embedding or database write fails after retries.
    """
    try:
        # Reconstruct the list of clean Document objects using the surviving chunk IDs.
        valid_ids = set(df_filtered["chunk_id"].tolist())
        clean_docs = [doc for i, doc in enumerate(all_chunks) if i in valid_ids]
        logger.info(f"Embedding {len(clean_docs)} clean chunk(s) into ChromaDB...")

        # Optional hard reset to avoid duplicate / stale vectors between rebuilds.
        if RESET_CHROMA_ON_REBUILD and Path(CHROMA_DB_DIR).exists():
            logger.info("RESET_CHROMA_ON_REBUILD=true → removing previous chroma_db before re-embedding...")
            
            # Clear ChromaDB's internal client cache so we don't hold a stale SQLite connection
            try:
                import chromadb
                chromadb.api.client.SharedSystemClient.clear_system_cache()
            except Exception as e:
                logger.warning(f"Could not clear Chroma cache: {e}")
                
            shutil.rmtree(CHROMA_DB_DIR, ignore_errors=True)
            Path(CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)

        # Local embeddings — runs on CPU, no API key or quota required.
        # The model is downloaded once (~80 MB) and cached automatically.
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},  # Cosine similarity requires normalised vectors.
        )
        logger.info(f"Using local embedding model: {EMBEDDING_MODEL}")

        # ---------------------------------------------------------------------------
        # Local batch processing — no API rate limits to worry about.
        # Batching is still used to manage memory efficiently on CPU.
        # ---------------------------------------------------------------------------
        BATCH_SIZE = 256         # Larger batches are fine locally (no quota).
        SLEEP_SECONDS = 0        # No need to pause between batches.
        RETRY_WAIT = 0           # No retries needed — no network calls.

        total = len(clean_docs)
        batches = [clean_docs[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
        total_batches = len(batches)
        logger.info(f"Processing {total_batches} batch(es) of up to {BATCH_SIZE} chunks each.")

        # --- Build ChromaDB in batches (memory-efficient on CPU) ---
        vector_db = None
        for batch_num, batch in enumerate(batches, start=1):
            if vector_db is None:
                # First batch — create the ChromaDB collection from scratch.
                vector_db = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=CHROMA_DB_DIR,
                )
            else:
                # Subsequent batches — append to the existing collection.
                vector_db.add_documents(batch)

            embedded_so_far = min(batch_num * BATCH_SIZE, total)
            logger.info(
                f"  ✅ Batch {batch_num}/{total_batches} embedded "
                f"({embedded_so_far}/{total} chunks)"
            )

        doc_count = len(vector_db.get()["ids"]) if vector_db else 0
        logger.info(f"✅ ChromaDB populated with {doc_count} vectors at '{CHROMA_DB_DIR}'.")
        return vector_db

    except Exception as e:
        logger.error(f"ChromaDB embedding failed: {e}")
        raise


# ===========================================================================
# ORCHESTRATOR — Run the full pipeline end-to-end
# ===========================================================================

def run_pipeline():
    """
    Orchestrates all 6 steps of the Data Science processing pipeline.

    This function is called by app.py's "Rebuild Knowledge Base" button
    and can also be run directly from the command line.

    Pipeline Order:
      LOAD → CHUNK → ANALYZE → FILTER → VISUALIZE → EMBED → STORE

    Returns:
        Tuple[pd.DataFrame | None, Chroma | None]:
          - The filtered DataFrame (for inspection/display in the UI).
          - The populated Chroma vector store (for immediate querying).
          Returns (None, None) if no documents are found.
    """
    logger.info("🔬 Starting PAGie Data Science Pipeline...")

    # Step 1: Load raw documents
    documents = load_documents()
    if not documents:
        logger.error(
            "❌ No documents found in ./data/. "
            "Please run sync_data.py first to download your files."
        )
        return None, None

    # Step 2: Chunk into RAG-sized pieces
    chunks = chunk_documents(documents)

    # Step 3: Build statistical DataFrame
    df_raw = build_dataframe(chunks)

    # Step 4: Apply semantic filtering to remove empty/invalid chunks
    df_filtered = apply_semantic_filter(df_raw)

    # Step 5: Generate EDA visualizations for the project report
    generate_eda_plots(df_raw, df_filtered)

    # Step 6: Embed clean chunks and store in ChromaDB
    vector_db = embed_and_store(df_filtered, chunks)

    logger.info("🎉 PAGie Data Science Pipeline complete!")
    logger.info(f"   Total raw chunks     : {len(df_raw)}")
    logger.info(f"   Chunks after filter  : {len(df_filtered)}")
    logger.info(f"   Artifacts removed    : {len(df_raw) - len(df_filtered)}")
    logger.info("   EDA report           : ./assets/eda_report.png")
    logger.info(f"   Vector DB            : {CHROMA_DB_DIR}/")

    return df_filtered, vector_db


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df, db = run_pipeline()
    if df is not None:
        print(f"\n✅ Done. {len(df)} clean chunks are now indexed in ChromaDB.")
        print("   Run app.py to start the PAGie chatbot.")
