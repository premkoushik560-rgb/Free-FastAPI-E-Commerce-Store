from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import require_admin
from database import get_db
from models import Category, User
from schemas import CategoryCreate, CategoryOut

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)).all())


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Category:
    category = Category(name=payload.name.strip(), slug=payload.slug, description=payload.description.strip())
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A category with that name or slug already exists.")
    db.refresh(category)
    return category

