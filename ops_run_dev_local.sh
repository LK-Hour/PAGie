#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama is not installed. Install it first: https://ollama.com"
  exit 1
fi

echo "Ensuring local model exists: qwen3.5:2b"
ollama pull qwen3.5:2b

if [ -f .env ]; then
  if grep -q '^APP_MODE=' .env; then
    sed -i 's/^APP_MODE=.*/APP_MODE=dev/' .env
  else
    echo 'APP_MODE=dev' >> .env
  fi
else
  cp .env.example .env
  echo 'APP_MODE=dev' >> .env
fi

echo "Starting PAGie in DEV mode (local LLM)..."
streamlit run app.py
