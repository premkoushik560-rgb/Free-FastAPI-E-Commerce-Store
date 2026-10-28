from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from auth.dependencies import get_current_user
from database import get_db
from models import CartItem, Product, User
from schemas import CartItemCreate, CartItemOut, CartItemUpdate, CartOut

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])


def cart_response(db: Session, user_id: int) -> CartOut:
    items = db.scalars(
        select(CartItem)
        .options(joinedload(CartItem.product).joinedload(Product.category))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.id)
    ).unique().all()
    mapped_items = [
        CartItemOut(
            id=item.id,
            quantity=item.quantity,
            product=item.product,
            line_total=item.product.price * item.quantity,
        )
        for item in items
    ]
    subtotal = sum((item.line_total for item in mapped_items), Decimal("0.00"))
    return CartOut(items=mapped_items, count=sum(item.quantity for item in items), subtotal=subtotal)


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    return cart_response(db, user.id)


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_cart_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    existing = db.scalar(select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id))
    target_quantity = payload.quantity + (existing.quantity if existing else 0)
    if target_quantity > product.stock:
        raise HTTPException(status_code=409, detail=f"Only {product.stock} of this item are currently in stock.")
    if existing:
        existing.quantity = target_quantity
    else:
        db.add(CartItem(user_id=user.id, product_id=product.id, quantity=payload.quantity))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This item could not be added to your cart.")
    return cart_response(db, user.id)


@router.patch("/items/{item_id}", response_model=CartOut)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    item = db.scalar(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.id == item_id, CartItem.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    if payload.quantity > item.product.stock:
        raise HTTPException(status_code=409, detail=f"Only {item.product.stock} of this item are currently in stock.")
    item.quantity = payload.quantity
    db.commit()
    return cart_response(db, user.id)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    db.delete(item)
    db.commit()
    return cart_response(db, user.id)

