from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from config import ACCESS_TOKEN_MINUTES, JWT_ALGORITHM, JWT_SECRET

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is missing. Set it in the local .env file before starting the app.")
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def read_access_token(token: str) -> int:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is missing. Set it in the local .env file before starting the app.")
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    subject = payload.get("sub")
    if not subject or not str(subject).isdigit():
        raise jwt.InvalidTokenError("Invalid token subject")
    return int(subject)

