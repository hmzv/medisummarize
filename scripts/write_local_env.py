"""Write a local .env for development. Do not print secret values."""

from __future__ import annotations

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / "data" / "runtime"
runtime.mkdir(parents=True, exist_ok=True)
db_path = (runtime / "medisummarize.dev.db").resolve().as_posix()
env_path = ROOT / ".env"
if env_path.exists():
    raise SystemExit("refused: .env already exists")

secret = secrets.token_urlsafe(48)
content = (
    "APP_NAME=MediSummarize AI\n"
    "APP_ENV=development\n"
    f"SECRET_KEY={secret}\n"
    f"DATABASE_URL=sqlite:///{db_path}\n"
    "CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173\n"
    "STORAGE_DIR=./storage\n"
    "VITE_API_BASE_URL=\n"
)
env_path.write_text(content, encoding="utf-8")
print("wrote_env=yes")
print("database_backend=sqlite")
