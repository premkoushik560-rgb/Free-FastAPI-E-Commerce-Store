from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from auth.security import create_access_token, hash_password, verify_password
from config import ACCESS_TOKEN_MINUTES, APP_ENV
from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="store_session",
        value=token,
        httponly=True,
        secure=APP_ENV == "production",
        samesite="lax",
        max_age=ACCESS_TOKEN_MINUTES * 60,
        path="/",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, response: Response, db: Session = Depends(get_db)) -> User:
    normalized_email = str(payload.email).lower()
    existing = db.scalar(select(User).where(User.email == normalized_email))
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(name=payload.name.strip(), email=normalized_email, password_hash=hash_password(payload.password), role="customer")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(user)
    set_session_cookie(response, create_access_token(user.id))
    return user


@router.post("/login", response_model=UserOut)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    set_session_cookie(response, create_access_token(user.id))
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("store_session", path="/", httponly=True, samesite="lax")
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user

