from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from auth.dependencies import get_current_user
from database import get_db
from models import CartItem, Order, OrderItem, Product, User
from schemas import CheckoutCreate, OrderOut

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def order_query():
    return select(Order).options(selectinload(Order.items))


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CheckoutCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Order:
    cart_items = db.scalars(
        select(CartItem)
        .options(joinedload(CartItem.product))
        .where(CartItem.user_id == user.id)
        .order_by(CartItem.id)
    ).unique().all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Your cart is empty.")

    for item in cart_items:
        if item.product.stock < item.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Not enough stock for {item.product.title}. Update your cart and try again.",
            )

    total = sum((item.product.price * item.quantity for item in cart_items), Decimal("0.00"))
    payment_succeeded = payload.payment_result == "success"
    order = Order(
        user_id=user.id,
        status="processing" if payment_succeeded else "payment_failed",
        payment_status="paid" if payment_succeeded else "failed",
        total=total,
        shipping_name=payload.shipping_name.strip(),
        shipping_address=payload.shipping_address.strip(),
        shipping_city=payload.shipping_city.strip(),
        shipping_postal_code=payload.shipping_postal_code.strip(),
        shipping_country=payload.shipping_country.strip(),
    )
    order.items = [
        OrderItem(
            product_id=item.product.id,
            product_title=item.product.title,
            quantity=item.quantity,
            unit_price=item.product.price,
        )
        for item in cart_items
    ]
    db.add(order)

    if payment_succeeded:
        for item in cart_items:
            result = db.execute(
                update(Product)
                .where(Product.id == item.product_id, Product.stock >= item.quantity)
                .values(stock=Product.stock - item.quantity)
            )
            if result.rowcount != 1:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=f"Stock changed for {item.product.title}. Your cart was not charged; please review it.",
                )
        for item in cart_items:
            db.delete(item)

    db.commit()
    return db.scalar(order_query().where(Order.id == order.id))


@router.get("", response_model=list[OrderOut])
def list_my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Order]:
    return list(
        db.scalars(order_query().where(Order.user_id == user.id).order_by(Order.created_at.desc(), Order.id.desc())).unique().all()
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_my_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Order:
    order = db.scalar(order_query().where(Order.id == order_id, Order.user_id == user.id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

