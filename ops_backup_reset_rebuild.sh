#!/usr/bin/env bash
set -euo pipefail

# PAGie ops script:
# 1) backup data + chroma db
# 2) optionally clean noisy raw files
# 3) reset vector db
# 4) rebuild embeddings

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$ROOT_DIR/backups/$TS"

mkdir -p "$BACKUP_DIR"

echo "[1/5] Backing up current state to: $BACKUP_DIR"
[ -d "$ROOT_DIR/chroma_db" ] && cp -a "$ROOT_DIR/chroma_db" "$BACKUP_DIR/" || true
[ -d "$ROOT_DIR/data" ] && cp -a "$ROOT_DIR/data" "$BACKUP_DIR/" || true
[ -f "$ROOT_DIR/.env" ] && cp "$ROOT_DIR/.env" "$BACKUP_DIR/.env.snapshot" || true


echo "[2/5] Optional noisy file cleanup (safe defaults)"
# Only remove obvious noisy artifacts from raw drive sync cache.
# Comment these lines out if you want zero cleanup.
if [ -d "$ROOT_DIR/data/drive" ]; then
  find "$ROOT_DIR/data/drive" -type f \( \
    -iname "*benchmark*" -o \
    -iname "*recovery-codes*" -o \
    -iname "*invoice*" -o \
    -iname "*test_malicious*" -o \
    -iname "*SETUP_COMPLETE*" \
  \) -print -delete || true
fi


echo "[3/5] Resetting vector DB"
rm -rf "$ROOT_DIR/chroma_db"


echo "[4/5] Rebuilding knowledge base"
python data_science_eda.py


echo "[5/5] Done"
echo "Backup: $BACKUP_DIR"
echo "Vector DB rebuilt successfully."
