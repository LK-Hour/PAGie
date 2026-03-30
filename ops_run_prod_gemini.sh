#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo ".env not found. Create it from .env.example first."
  exit 1
fi

if grep -q '^APP_MODE=' .env; then
  sed -i 's/^APP_MODE=.*/APP_MODE=prod/' .env
else
  echo 'APP_MODE=prod' >> .env
fi

echo "Starting PAGie in PROD mode (Gemini)..."
streamlit run app.py
