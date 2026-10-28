from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: Literal["customer", "admin"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str = Field(min_length=2, max_length=90, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(default="", max_length=240)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str


class ProductCreate(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    slug: str = Field(min_length=2, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(min_length=8, max_length=5000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category_id: int = Field(gt=0)
    image_url: str = Field(default="/static/images/objects.svg", max_length=500)
    stock: int = Field(ge=0, le=100000)


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=140)
    slug: str | None = Field(default=None, min_length=2, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, min_length=8, max_length=5000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    category_id: int | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    stock: int | None = Field(default=None, ge=0, le=100000)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str
    price: Decimal
    category_id: int
    image_url: str
    stock: int
    created_at: datetime
    category: CategoryOut


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    pages: int


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartItemOut(BaseModel):
    id: int
    quantity: int
    product: ProductOut
    line_total: Decimal


class CartOut(BaseModel):
    items: list[CartItemOut]
    count: int
    subtotal: Decimal


class CheckoutCreate(BaseModel):
    shipping_name: str = Field(min_length=2, max_length=120)
    shipping_address: str = Field(min_length=5, max_length=240)
    shipping_city: str = Field(min_length=2, max_length=100)
    shipping_postal_code: str = Field(min_length=2, max_length=24)
    shipping_country: str = Field(min_length=2, max_length=80)
    payment_result: Literal["success", "failure"] = "success"


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    product_title: str
    quantity: int
    unit_price: Decimal


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    payment_status: str
    total: Decimal
    shipping_name: str
    shipping_address: str
    shipping_city: str
    shipping_postal_code: str
    shipping_country: str
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: Literal["processing", "shipped", "delivered", "cancelled"]


class AdminDashboard(BaseModel):
    product_count: int
    category_count: int
    order_count: int
    customer_count: int
    paid_revenue: Decimal
    low_stock_count: int
    recent_orders: list[OrderOut]

