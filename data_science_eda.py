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
from langchain_google_genai import GoogleGenerativeAIEmbeddings
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
    logger.info(f"\n--- Descriptive Statistics (before IQR) ---\n{df[['word_count', 'char_count']].describe().to_string()}")
    return df


# ===========================================================================
# STEP 4 — IQR FILTER: Remove statistical outliers
# ===========================================================================

def apply_iqr_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the Interquartile Range (IQR) method to remove word-count outliers.

    The IQR is a non-parametric, robust statistical method for detecting
    outliers that does not assume a normal distribution — ideal for
    text data which is typically right-skewed.

    Method:
      Q1    = 25th percentile of word_count
      Q3    = 75th percentile of word_count
      IQR   = Q3 - Q1  (the "middle 50%" spread)

      Lower Fence = Q1 - 1.5 × IQR  → chunks below this are too short
                                        (e.g., page numbers, stray headers)
      Upper Fence = Q3 + 1.5 × IQR  → chunks above this are too long
                                        (unbroken walls of text with no focus)

    Why this matters for RAG:
      Short chunks lack sufficient context to be meaningful.
      Long chunks dilute the specific information the LLM needs.
      IQR filtering ensures every chunk fed to Gemini is optimally sized.

    Args:
        df: DataFrame with a 'word_count' column.

    Returns:
        A filtered DataFrame containing only inlier chunks.
    """
    Q1 = df["word_count"].quantile(0.25)
    Q3 = df["word_count"].quantile(0.75)
    IQR = Q3 - Q1
    lower_fence = Q1 - 1.5 * IQR
    upper_fence = Q3 + 1.5 * IQR

    logger.info("\n--- IQR Outlier Analysis ---")
    logger.info(f"  Q1  (25th percentile) : {Q1:.1f} words")
    logger.info(f"  Q3  (75th percentile) : {Q3:.1f} words")
    logger.info(f"  IQR                   : {IQR:.1f} words")
    logger.info(f"  Lower Fence           : {lower_fence:.1f} words  (minimum quality threshold)")
    logger.info(f"  Upper Fence           : {upper_fence:.1f} words  (maximum quality threshold)")

    # Apply the IQR bounds to retain only the statistically 'normal' chunks.
    df_filtered = df[
        (df["word_count"] >= lower_fence) & (df["word_count"] <= upper_fence)
    ].copy()

    removed = len(df) - len(df_filtered)
    logger.info(f"  Outliers removed      : {removed} chunks ({removed / len(df) * 100:.1f}%)")
    logger.info(f"  Clean chunks retained : {len(df_filtered)} chunks")

    return df_filtered


# ===========================================================================
# STEP 5 — VISUALIZE: Generate EDA plots as per the project proposal
# ===========================================================================

def generate_eda_plots(df_raw: pd.DataFrame, df_filtered: pd.DataFrame):
    """
    Generates and saves a 2×2 panel of EDA visualizations to ./assets/eda_report.png.

    The four charts fulfil the exact EDA requirements from the project proposal:

      [Top-Left]  Histogram  — Chunk word count distribution, before vs. after IQR.
                               Shows how IQR filtering tightens the distribution.

      [Top-Right] Boxplot    — Comparing word count spread between Notion and Google Drive.
                               Expected insight: Notion pages are shorter and more structured.

      [Bot-Left]  Pie Chart  — Proportion of cleaned knowledge base by source platform.
                               Shows which platform contributes more data.

      [Bot-Right] Scatter    — IQR outlier detection map. Red × marks = removed chunks.
                               Visually demonstrates where outliers were in the dataset.

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
    # Plot 1 (Top-Left): Histogram — Before vs. After IQR
    # -----------------------------------------------------------------------
    ax1 = axes[0, 0]
    ax1.hist(df_raw["word_count"], bins=30, alpha=0.45, color="#4C72B0", label="Before IQR")
    ax1.hist(df_filtered["word_count"], bins=30, alpha=0.75, color="#55A868", label="After IQR")
    ax1.set_title("Chunk Word Count Distribution\n(Before vs. After IQR Filtering)")
    ax1.set_xlabel("Word Count per Chunk")
    ax1.set_ylabel("Number of Chunks")
    ax1.legend()
    ax1.axvline(df_filtered["word_count"].mean(), color="darkgreen", linestyle="--",
                linewidth=1.5, label=f'Mean: {df_filtered["word_count"].mean():.0f}')

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
    # Plot 4 (Bot-Right): Scatter — IQR outlier detection map
    # -----------------------------------------------------------------------
    ax4 = axes[1, 1]
    Q1 = df_raw["word_count"].quantile(0.25)
    Q3 = df_raw["word_count"].quantile(0.75)
    IQR_val = Q3 - Q1
    lower_fence = Q1 - 1.5 * IQR_val
    upper_fence = Q3 + 1.5 * IQR_val

    is_outlier = (
        (df_raw["word_count"] < lower_fence) | (df_raw["word_count"] > upper_fence)
    )

    # Plot inliers (kept) and outliers (removed) with distinct styles.
    ax4.scatter(
        df_raw.index[~is_outlier],
        df_raw.loc[~is_outlier, "word_count"],
        alpha=0.4, s=12, color="#55A868", label="Kept",
    )
    ax4.scatter(
        df_raw.index[is_outlier],
        df_raw.loc[is_outlier, "word_count"],
        alpha=0.9, s=30, color="#C44E52", label="Removed (Outlier)", marker="x",
    )
    # Draw the IQR fence lines to make the decision boundary visible.
    ax4.axhline(lower_fence, color="orange", linestyle="--", linewidth=1.8,
                label=f"Lower Fence ({lower_fence:.0f} words)")
    ax4.axhline(upper_fence, color="red", linestyle="--", linewidth=1.8,
                label=f"Upper Fence ({upper_fence:.0f} words)")
    ax4.set_title("IQR Outlier Detection Map")
    ax4.set_xlabel("Chunk Index")
    ax4.set_ylabel("Word Count")
    ax4.legend(fontsize=9)

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
    Embeds IQR-filtered text chunks using Google's embedding model
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

        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

        # ---------------------------------------------------------------------------
        # Rate-limited batching with checkpoint/resume support.
        #
        # The free-tier Gemini API enforces two separate limits:
        #   • RPM (requests/minute): causes temporary 429s — solved by waiting 65s.
        #   • RPD (requests/day):    causes permanent 429s until midnight UTC reset.
        #
        # We differentiate by checking the error message:
        #   - Daily quota: message contains "billing" or "check your plan"
        #   - Per-minute:  all other 429 / RESOURCE_EXHAUSTED errors
        #
        # A JSON checkpoint file (CHECKPOINT_FILE) tracks which batch was last
        # successfully embedded. On the next run the script resumes from that
        # batch and reuses the existing ChromaDB, so no work is duplicated.
        # ---------------------------------------------------------------------------
        BATCH_SIZE = 80          # Chunks per API call (safe under the 100 req/min limit).
        SLEEP_SECONDS = 0.8      # Pause between batches → ~75 calls/min max.
        RETRY_WAIT = 65          # Seconds to wait on a per-minute 429 error.

        total = len(clean_docs)
        batches = [clean_docs[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
        total_batches = len(batches)
        logger.info(f"Processing {total_batches} batch(es) of up to {BATCH_SIZE} chunks each.")

        # --- Load checkpoint (if a previous run was interrupted by daily quota) ---
        start_batch = 0
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE) as f:
                    checkpoint = json.load(f)
                start_batch = checkpoint.get("next_batch", 0)
                logger.info(
                    f"📂 Checkpoint found — resuming from batch {start_batch + 1}/{total_batches} "
                    f"({start_batch * BATCH_SIZE}/{total} chunks already embedded)."
                )
            except (json.JSONDecodeError, KeyError):
                logger.warning("Checkpoint file corrupt — starting from batch 1.")
                start_batch = 0

        # --- Load existing ChromaDB if resuming, otherwise start fresh ---
        vector_db = None
        chroma_db_path = Path(CHROMA_DB_DIR)
        if start_batch > 0 and chroma_db_path.exists():
            try:
                vector_db = Chroma(
                    persist_directory=CHROMA_DB_DIR,
                    embedding_function=embeddings,
                )
                logger.info("Loaded existing ChromaDB collection for resume.")
            except Exception as load_err:
                logger.warning(f"Could not load existing ChromaDB ({load_err}). Starting from batch 1.")
                start_batch = 0
                vector_db = None

        # --- Main embedding loop ---
        for batch_num, batch in enumerate(batches, start=1):
            # Skip batches that were already embedded in a previous run.
            if batch_num <= start_batch:
                continue

            success = False
            while not success:
                try:
                    if vector_db is None:
                        # First-ever batch — create the ChromaDB collection from scratch.
                        vector_db = Chroma.from_documents(
                            documents=batch,
                            embedding=embeddings,
                            persist_directory=CHROMA_DB_DIR,
                        )
                    else:
                        # All subsequent batches — append to the existing collection.
                        vector_db.add_documents(batch)

                    # Save checkpoint so the next run can resume from here.
                    with open(CHECKPOINT_FILE, "w") as f:
                        json.dump({"next_batch": batch_num}, f)

                    embedded_so_far = min(batch_num * BATCH_SIZE, total)
                    logger.info(
                        f"  ✅ Batch {batch_num}/{total_batches} embedded "
                        f"({embedded_so_far}/{total} chunks)"
                    )
                    success = True

                except Exception as batch_err:
                    err_str = str(batch_err)
                    # Distinguish daily quota exhaustion from per-minute rate limiting.
                    is_daily_quota = (
                        "billing" in err_str.lower()
                        or "check your plan" in err_str.lower()
                    )
                    is_rate_limit = (
                        "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                    )

                    if is_daily_quota:
                        # Daily quota is exhausted — retrying will not help today.
                        logger.error(
                            "\n❌ DAILY API QUOTA EXHAUSTED\n"
                            f"   Successfully embedded {(batch_num - 1) * BATCH_SIZE}/{total} chunks "
                            f"across {batch_num - 1}/{total_batches} batches.\n"
                            "   Progress has been saved to the checkpoint file.\n"
                            "   Re-run this script tomorrow (quota resets at midnight UTC) "
                            "to continue from where it left off.\n"
                        )
                        # Return partial DB — app.py can still query what was indexed.
                        return vector_db
                    elif is_rate_limit:
                        # Per-minute rate limit — pause and retry automatically.
                        logger.warning(
                            f"  ⚠️  Per-minute rate limit hit on batch {batch_num}. "
                            f"Waiting {RETRY_WAIT}s before retrying..."
                        )
                        time.sleep(RETRY_WAIT)
                    else:
                        # Unknown error — do not retry, raise immediately.
                        raise

            # Polite pause between successful batches to respect the per-minute quota.
            if batch_num < total_batches:
                time.sleep(SLEEP_SECONDS)

        # All batches complete — delete the checkpoint file (no longer needed).
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
            logger.info("🗑️  Checkpoint cleared — all batches complete.")

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
    logger.info(f"   Chunks after IQR     : {len(df_filtered)}")
    logger.info(f"   Outliers removed     : {len(df_raw) - len(df_filtered)}")
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
