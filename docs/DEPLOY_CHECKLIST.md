# PAGie Deploy Checklist

## 1) Environment
- [ ] `python -m venv venv && source venv/bin/activate`
- [ ] `pip install -r requirements.txt`
- [ ] `cp .env.example .env`

## 2) Secrets
- [ ] Set `GOOGLE_API_KEY`
- [ ] Set `GOOGLE_DRIVE_FOLDER_ID` (recommended to reduce noisy ingestion)
- [ ] Set `NOTION_TOKEN` and `NOTION_DATABASE_ID` (if Notion is used)
- [ ] Ensure `client_secret_*.json` and `token.json` are not committed

## 3) Dev mode (local LLM)
- [ ] Install/start Ollama
- [ ] `./ops_run_dev_local.sh`
- [ ] In sidebar, verify: `Mode: dev`, `LLM: ollama (qwen3.5:0.8b)`

## 4) Rebuild clean vector DB
- [ ] `./ops_backup_reset_rebuild.sh`
- [ ] Verify `assets/eda_report.png` is updated
- [ ] Verify chunk count in sidebar

## 5) Prod mode (Gemini)
- [ ] Set `APP_MODE=prod` (or run `./ops_run_prod_gemini.sh`)
- [ ] Verify: `Mode: prod`, `LLM: gemini (...)`
- [ ] Run sanity questions from test set

## 6) Demo readiness
- [ ] Keep fallback enabled: `ALLOW_429_FALLBACK_TO_LOCAL=true`
- [ ] Prepare 5 known questions + expected sources
- [ ] Confirm no secrets in git status before final push
