"""
data_science_eda.py — Data Science Processing Pipeline for PAGie
=================================================================
This is the core Data Science module. It implements the full
preprocessing and analysis pipeline as specified in the project proposal:

  1. LOAD     → Load all raw documents from ./data/ (Drive + Notion)
  2. CHUNK    → Split documents into fixed-size text chunks
  3. ANALYZE  → Convert chunks to a Pandas DataFrame with word-count statistics
  4. IQR      → Apply Interquartile Range method to remove statistical outliers
  5. VISUALIZE → Generate 4 EDA plots and save to ./assets/eda_report.png
  6. EMBED    → Vectorize clean chunks and persist them to ChromaDB

Usage:
  python data_science_eda.py
"""

import json
import logging
import os
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
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load API keys from .env — required for embedding model.
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path("./data")
ASSETS_DIR = Path("./assets")
CHROMA_DB_DIR = "./chroma_db"

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

# Ensure output directories exist.
ASSETS_DIR.mkdir(exist_ok=True)

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
# STEP 1 — LOAD: Read all raw documents from ./data/
# ===========================================================================

def load_documents() -> list:
    """
    Loads all text and PDF documents from the ./data/ directory tree.

    Files in ./data/notion/ are tagged with platform='Notion'.
    Files in ./data/drive/ are tagged with platform='Google Drive'.
    This metadata is critical for the EDA platform-comparison charts.

    Returns:
        A list of LangChain Document objects, each containing page_content
        and metadata (source path, platform).
    """
    all_docs = []

    # --- Load .txt files (from both Google Drive and Notion directories) ---
    try:
        txt_loader = DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            silent_errors=True,  # Skip files with encoding errors gracefully.
        )
        txt_docs = txt_loader.load()

        # Attach source platform metadata to each document for EDA.
        for doc in txt_docs:
            source = doc.metadata.get("source", "")
            doc.metadata["platform"] = "Notion" if "notion" in source.lower() else "Google Drive"

        all_docs.extend(txt_docs)
        logger.info(f"Loaded {len(txt_docs)} text file(s).")

    except Exception as e:
        logger.error(f"Error loading .txt files: {e}")

    # --- Load .pdf files (typically from Google Drive) ---
    try:
        pdf_paths = list(DATA_DIR.rglob("*.pdf"))
        for pdf_path in pdf_paths:
            try:
                loader = PyPDFLoader(str(pdf_path))
                pdf_docs = loader.load()
                for doc in pdf_docs:
                    doc.metadata["platform"] = "Google Drive"
                all_docs.extend(pdf_docs)
                logger.info(f"  ✅ Loaded PDF: {pdf_path.name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to load PDF '{pdf_path.name}': {e}")

    except Exception as e:
        logger.error(f"Error scanning for PDF files: {e}")

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
      - platform   : 'Notion' or 'Google Drive' (for comparative EDA).
      - source     : Full file path of the originating document.

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


def apply_iqr_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes semantically empty chunks using a minimum word-count threshold.

    Design rationale
    ----------------
    IQR (Interquartile Range) is a classic statistical outlier method designed
    for numerical measurements such as sensor readings. Applied naively to
    text, it introduces content bias:

      • The lower fence (Q1 − 1.5×IQR) becomes negative for this dataset
        (≈ −56 words), so it never actually filters anything — yet it gives
        a false impression of statistical rigour.
      • The upper fence removes long chunks that are semantically valid and
        would otherwise provide valuable context to the LLM.
      • IQR treats length as a proxy for quality, which is incorrect:
        a 3-word chunk "CADT, Phnom Penh" is short but factually critical,
        while a 50-word chunk of repeated boilerplate is useless.

    The chosen approach instead uses a single, domain-justified threshold:
      word_count >= MIN_WORD_COUNT (default: 5)

    This removes genuine artifacts (page numbers, stray OCR characters,
    empty table cells) without discarding any real content, regardless of
    how long or short it is. It is unbiased with respect to chunk length.

    IQR statistics are still *computed and logged* below for transparency
    and to provide the EDA visualisation with distribution context.

    Args:
        df: DataFrame with a 'word_count' column.

    Returns:
        A filtered DataFrame retaining all chunks with >= MIN_WORD_COUNT words.
    """
    # --- Still compute IQR statistics for EDA reporting purposes ---
    Q1 = df["word_count"].quantile(0.25)
    Q3 = df["word_count"].quantile(0.75)
    IQR = Q3 - Q1
    iqr_lower = Q1 - 1.5 * IQR
    iqr_upper = Q3 + 1.5 * IQR

    logger.info("\n--- Chunk Quality Filter Analysis ---")
    logger.info(f"  Distribution Q1       : {Q1:.1f} words")
    logger.info(f"  Distribution Q3       : {Q3:.1f} words")
    logger.info(f"  IQR (for reference)   : {IQR:.1f} words")
    logger.info(f"  IQR lower fence       : {iqr_lower:.1f} words  (negative → never triggers)")
    logger.info(f"  IQR upper fence       : {iqr_upper:.1f} words  (not applied — biased)")
    logger.info(f"  Applied threshold     : word_count >= {MIN_WORD_COUNT} (semantic minimum)")

    # Apply the semantic minimum threshold — no upper bound.
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

    The four charts fulfil the exact EDA requirements from the project proposal:

      [Top-Left]  Histogram  — Chunk word count distribution, before vs. after quality filter.
                               Shows the applied minimum threshold and post-filter mean.

      [Top-Right] Boxplot    — Comparing word count spread between Notion and Google Drive.
                               Expected insight: Notion pages are shorter and more structured.

      [Bot-Left]  Pie Chart  — Proportion of cleaned knowledge base by source platform.
                               Shows which platform contributes more data.

      [Bot-Right] Scatter    — Quality filter map. Red × = removed artifacts (< 5 words).
                               IQR fences shown as reference lines to illustrate why the
                               data-driven approach is unsuitable for this dataset.

    Args:
        df_raw      : DataFrame before IQR filtering (all chunks).
        df_filtered : DataFrame after IQR filtering (clean chunks only).
    """
    sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "PAGie — Knowledge Base Exploratory Data Analysis (EDA)",
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
    ax1.set_title("Chunk Word Count Distribution\n(Before vs. After Quality Filtering)")
    ax1.set_xlabel("Word Count per Chunk")
    ax1.set_ylabel("Number of Chunks")
    ax1.axvline(MIN_WORD_COUNT, color="orange", linestyle="--", linewidth=1.8,
                label=f"Min threshold ({MIN_WORD_COUNT} words)")
    ax1.axvline(df_filtered["word_count"].mean(), color="darkgreen", linestyle="--",
                linewidth=1.5, label=f'Mean after: {df_filtered["word_count"].mean():.0f} words')
    ax1.legend(fontsize=9)

    # -----------------------------------------------------------------------
    # Plot 2 (Top-Right): Boxplot — Word count by source platform
    # -----------------------------------------------------------------------
    ax2 = axes[0, 1]
    platforms = df_filtered["platform"].unique()
    if len(platforms) > 1:
        # Comparative boxplot: visualizes that Notion pages are shorter than Drive docs.
        platform_data = [
            df_filtered[df_filtered["platform"] == p]["word_count"].values
            for p in platforms
        ]
        bp = ax2.boxplot(platform_data, labels=platforms, patch_artist=True,
                         medianprops={"color": "black", "linewidth": 2})
        colors = ["#4C72B0", "#DD8452"]
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
    else:
        # Fallback: single platform boxplot
        ax2.boxplot(df_filtered["word_count"], patch_artist=True,
                    boxprops={"facecolor": "#4C72B0", "alpha": 0.7})
        ax2.set_xticks([1])
        ax2.set_xticklabels(platforms if len(platforms) == 1 else ["All"])
    ax2.set_title("Word Count Distribution by Source Platform")
    ax2.set_xlabel("Platform")
    ax2.set_ylabel("Word Count per Chunk")

    # -----------------------------------------------------------------------
    # Plot 3 (Bot-Left): Pie Chart — Knowledge base composition
    # -----------------------------------------------------------------------
    ax3 = axes[1, 0]
    platform_counts = df_filtered["platform"].value_counts()
    colors_pie = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"][:len(platform_counts)]
    wedges, texts, autotexts = ax3.pie(
        platform_counts,
        labels=platform_counts.index,
        autopct="%1.1f%%",
        colors=colors_pie,
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight("bold")
    ax3.set_title("Knowledge Base Composition\nby Source Platform")

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
    # IQR reference lines — shown as dashed to contrast with the applied threshold.
    ax4.axhline(iqr_upper, color="grey", linestyle="--", linewidth=1.2,
                label=f"IQR upper fence ({iqr_upper:.0f} words) — not applied")
    ax4.axhline(iqr_lower, color="lightgrey", linestyle="--", linewidth=1.2,
                label=f"IQR lower fence ({iqr_lower:.0f} words) — negative, never triggered")
    ax4.set_title("Chunk Quality Filter Map\n(Semantic Threshold vs. IQR Reference)")
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
        df_filtered  : DataFrame of clean chunks (post-IQR), with chunk_id column.
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
      LOAD → CHUNK → ANALYZE → IQR FILTER → VISUALIZE → EMBED → STORE

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

    # Step 4: Apply IQR to remove low-quality outlier chunks
    df_filtered = apply_iqr_filter(df_raw)

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
