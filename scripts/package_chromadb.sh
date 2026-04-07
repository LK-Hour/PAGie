#!/bin/bash
# package_chromadb.sh — Prepare ChromaDB for Streamlit Cloud Deployment
# ===========================================================================
# This script packages your local ChromaDB for cloud deployment by copying
# it to the repository structure where it can be committed to Git.

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 PAGie ChromaDB Packaging Tool${NC}"
echo "========================================"
echo ""

# Source and destination paths
SOURCE_DIR="./chroma_db"
DEST_DIR="./data/chromadb_prebuilt/chroma_db"
BACKUP_ARCHIVE="chromadb_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

# Check if source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Error: ChromaDB not found at $SOURCE_DIR${NC}"
    echo "Please run data sync first to create the vector database."
    exit 1
fi

# Check if source has data
FILE_COUNT=$(find "$SOURCE_DIR" -type f | wc -l)
if [ "$FILE_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ Error: ChromaDB is empty${NC}"
    echo "No files found in $SOURCE_DIR"
    exit 1
fi

echo -e "${GREEN}✅ Found ChromaDB with $FILE_COUNT files${NC}"
echo ""

# Calculate size
SOURCE_SIZE=$(du -sh "$SOURCE_DIR" | cut -f1)
echo "📊 Source size: $SOURCE_SIZE"
echo ""

# Ask user for confirmation
echo "This will:"
echo "  1. Create a backup archive: $BACKUP_ARCHIVE"
echo "  2. Copy ChromaDB to: $DEST_DIR"
echo "  3. Make it ready for git commit"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Create backup archive
echo ""
echo -e "${YELLOW}📦 Step 1: Creating backup archive...${NC}"
tar -czf "$BACKUP_ARCHIVE" "$SOURCE_DIR"
ARCHIVE_SIZE=$(du -sh "$BACKUP_ARCHIVE" | cut -f1)
echo -e "${GREEN}✅ Backup created: $BACKUP_ARCHIVE ($ARCHIVE_SIZE)${NC}"

# Check if archive is too large for GitHub
ARCHIVE_SIZE_MB=$(du -m "$BACKUP_ARCHIVE" | cut -f1)
if [ "$ARCHIVE_SIZE_MB" -gt 100 ]; then
    echo -e "${YELLOW}⚠️  Warning: Archive is ${ARCHIVE_SIZE_MB}MB (GitHub limit is 100MB)${NC}"
    echo "Consider using Google Cloud Storage (GCS) instead of committing to Git."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Step 2: Copy to destination
echo ""
echo -e "${YELLOW}📂 Step 2: Copying to repository structure...${NC}"
rm -rf "$DEST_DIR"  # Remove old version
mkdir -p "$DEST_DIR"

cp -r "$SOURCE_DIR"/* "$DEST_DIR/"
echo -e "${GREEN}✅ Copied to: $DEST_DIR${NC}"

# Step 3: Git status
echo ""
echo -e "${YELLOW}📝 Step 3: Git status...${NC}"
git status "$DEST_DIR" 2>/dev/null || echo "(Not in a git repository)"

# Final instructions
echo ""
echo -e "${GREEN}✅ PACKAGING COMPLETE!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Add to Git:"
echo "   git add data/chromadb_prebuilt/"
echo "   git commit -m 'Add pre-built ChromaDB for cloud deployment'"
echo "   git push"
echo ""
echo "2. Deploy to Streamlit Cloud:"
echo "   The app will automatically use the pre-built database"
echo ""
echo "3. Backup archive saved to: $BACKUP_ARCHIVE"
echo "   (Keep this safe - you can delete after successful deployment)"
echo ""
echo -e "${YELLOW}Note: The app will automatically detect and use this pre-built ChromaDB${NC}"
echo -e "${YELLOW}when deployed to Streamlit Cloud (see gcs_sync.py).${NC}"
echo ""
