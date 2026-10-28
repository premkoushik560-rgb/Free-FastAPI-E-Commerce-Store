from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from auth.dependencies import require_admin
from database import get_db
from models import CartItem, Category, Product, User
from schemas import ProductCreate, ProductOut, ProductPage, ProductUpdate

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("", response_model=ProductPage)
def list_products(
    q: str | None = Query(default=None, max_length=120),
    category_id: int | None = Query(default=None, gt=0),
    sort: str = Query(default="featured", pattern="^(featured|price_asc|price_desc|newest|name)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    db: Session = Depends(get_db),
) -> ProductPage:
    query = select(Product).options(joinedload(Product.category)).join(Category)
    count_query = select(func.count(Product.id)).join(Category)
    if q:
        term = f"%{q.strip()}%"
        condition = or_(Product.title.ilike(term), Product.description.ilike(term), Category.name.ilike(term))
        query = query.where(condition)
        count_query = count_query.where(condition)
    if category_id:
        query = query.where(Product.category_id == category_id)
        count_query = count_query.where(Product.category_id == category_id)

    ordering = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "newest": Product.created_at.desc(),
        "name": Product.title.asc(),
        "featured": Product.id.asc(),
    }[sort]
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(ordering).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return ProductPage(items=items, total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.scalar(select(Product).options(joinedload(Product.category)).where(Product.id == product_id))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Product:
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with that slug already exists.")
    db.refresh(product)
    return db.scalar(select(Product).options(joinedload(Product.category)).where(Product.id == product.id))


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    updates = payload.model_dump(exclude_unset=True)
    if not updates or any(value is None for value in updates.values()):
        raise HTTPException(status_code=422, detail="Provide at least one product field, and do not use null values.")
    if "category_id" in updates and db.get(Category, updates["category_id"]) is None:
        raise HTTPException(status_code=404, detail="Category not found.")
    for field, value in updates.items():
        setattr(product, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with that slug already exists.")
    db.refresh(product)
    return db.scalar(select(Product).options(joinedload(Product.category)).where(Product.id == product_id))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Response:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

