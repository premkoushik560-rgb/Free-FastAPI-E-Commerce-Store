from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="customer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    cart_items: Mapped[list[CartItem]] = relationship(back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[list[Order]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(90), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(240), default="")

    products: Mapped[list[Product]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(140), index=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    image_url: Mapped[str] = mapped_column(String(500), default="/static/images/objects.svg")
    stock: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    category: Mapped[Category] = relationship(back_populates="products")
    cart_items: Mapped[list[CartItem]] = relationship(back_populates="product")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[int] = mapped_column(default=1)
    user: Mapped[User] = relationship(back_populates="cart_items")
    product: Mapped[Product] = relationship(back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="processing", index=True)
    payment_status: Mapped[str] = mapped_column(String(20), default="paid")
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_name: Mapped[str] = mapped_column(String(120))
    shipping_address: Mapped[str] = mapped_column(String(240))
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_postal_code: Mapped[str] = mapped_column(String(24))
    shipping_country: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_title: Mapped[str] = mapped_column(String(140))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    order: Mapped[Order] = relationship(back_populates="items")

