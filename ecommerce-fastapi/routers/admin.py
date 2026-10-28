from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from auth.dependencies import require_admin
from database import get_db
from models import Category, Order, Product, User
from schemas import AdminDashboard, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])


@router.get("/dashboard", response_model=AdminDashboard)
def dashboard(db: Session = Depends(get_db), _admin: User = Depends(require_admin)) -> AdminDashboard:
    recent_orders = db.scalars(
        select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc(), Order.id.desc()).limit(6)
    ).unique().all()
    return AdminDashboard(
        product_count=db.scalar(select(func.count(Product.id))) or 0,
        category_count=db.scalar(select(func.count(Category.id))) or 0,
        order_count=db.scalar(select(func.count(Order.id))) or 0,
        customer_count=db.scalar(select(func.count(User.id)).where(User.role == "customer")) or 0,
        paid_revenue=db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(Order.payment_status == "paid")) or Decimal("0.00"),
        low_stock_count=db.scalar(select(func.count(Product.id)).where(Product.stock <= 5)) or 0,
        recent_orders=recent_orders,
    )


@router.get("/orders", response_model=list[OrderOut])
def list_all_orders(db: Session = Depends(get_db), _admin: User = Depends(require_admin)) -> list[Order]:
    return list(db.scalars(select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())).unique().all())


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Order:
    order = db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    if order.payment_status != "paid":
        raise HTTPException(status_code=409, detail="Only paid orders can be moved through fulfillment.")
    if order.status == "delivered" and payload.status != "delivered":
        raise HTTPException(status_code=409, detail="A delivered order cannot move back to an earlier status.")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order

