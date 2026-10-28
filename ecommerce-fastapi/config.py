"""Small local .env loader so the project needs no extra configuration package."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv_file() -> None:
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            os.environ.setdefault(key, value)


load_dotenv_file()

APP_DIR = Path(__file__).resolve().parent
# Replit may inject DATABASE_URL for unrelated workspace services. The store is
# intentionally SQLite-first; an alternate database must be opted into locally.
DATABASE_URL = os.getenv("NORTHSTAR_DATABASE_URL", f"sqlite:///{APP_DIR / 'store.db'}")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
APP_ENV = os.getenv("APP_ENV", "development")

