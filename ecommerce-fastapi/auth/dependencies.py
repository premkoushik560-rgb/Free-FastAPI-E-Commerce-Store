from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.security import read_access_token
from database import get_db
from models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("store_session")
    authorization = request.headers.get("Authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue.")
    try:
        user_id = read_access_token(token)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired. Please sign in again.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your account could not be found.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required.")
    return user

