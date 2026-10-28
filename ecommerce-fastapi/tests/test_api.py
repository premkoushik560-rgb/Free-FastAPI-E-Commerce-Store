from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from database import Base
from models import Category, Product
from services.seed import seed_sample_data
from tests.conftest import admin_client, register


def test_storefront_docs_and_local_illustrations_load(client):
    storefront = client.get("/")
    assert storefront.status_code == 200
    assert "Northstar Supply" in storefront.text
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    illustration = client.get("/static/images/hero.svg")
    assert illustration.status_code == 200
    assert "<svg" in illustration.text


def test_seed_is_idempotent_and_contains_the_sample_catalog(tmp_path):
    seed_engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    Base.metadata.create_all(bind=seed_engine)
    SeedSession = sessionmaker(bind=seed_engine, autoflush=False, expire_on_commit=False)
    with SeedSession() as db:
        seed_sample_data(db)
        seed_sample_data(db)
        assert db.scalar(select(func.count()).select_from(Category)) == 5
        assert db.scalar(select(func.count()).select_from(Product)) == 20
    seed_engine.dispose()


def test_registration_login_and_invalid_credentials(client):
    user = register(client)
    assert user["role"] == "customer"
    assert user["email"] == "customer@example.com"
    assert client.get("/api/v1/auth/me").json()["id"] == user["id"]

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    invalid = client.post("/api/v1/auth/login", json={"email": user["email"], "password": "wrong-password"})
    assert invalid.status_code == 401

    login = client.post("/api/v1/auth/login", json={"email": user["email"], "password": "correct-horse-1"})
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


def test_products_search_filter_pagination_and_details(client):
    listing = client.get("/api/v1/products?page=1&page_size=1&sort=price_asc")
    assert listing.status_code == 200
    assert listing.json()["total"] == 2
    assert listing.json()["pages"] == 2
    assert listing.json()["items"][0]["title"] == "Pocket Journal"

    search = client.get("/api/v1/products?q=desk")
    assert search.status_code == 200
    assert [item["title"] for item in search.json()["items"]] == ["Desk Tray"]

    detail = client.get("/api/v1/products/1")
    assert detail.status_code == 200
    assert detail.json()["category"]["name"] == "Everyday Carry"
    assert client.get("/api/v1/products/999").status_code == 404
    assert client.get("/health").json() == {"status": "ok"}


def test_cart_is_private_and_checks_stock(client):
    assert client.get("/api/v1/cart").status_code == 401
    register(client)

    added = client.post("/api/v1/cart/items", json={"product_id": 2, "quantity": 2})
    assert added.status_code == 201
    assert added.json()["count"] == 2
    cart_item_id = added.json()["items"][0]["id"]

    over_stock = client.patch(f"/api/v1/cart/items/{cart_item_id}", json={"quantity": 3})
    assert over_stock.status_code == 409
    updated = client.patch(f"/api/v1/cart/items/{cart_item_id}", json={"quantity": 1})
    assert updated.status_code == 200
    assert updated.json()["subtotal"] == "28.00"

    removed = client.delete(f"/api/v1/cart/items/{cart_item_id}")
    assert removed.status_code == 200
    assert removed.json()["items"] == []


def test_success_and_declined_orders_preserve_expected_stock_and_cart(client):
    register(client)
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 2})
    checkout = {
        "shipping_name": "Sample Customer",
        "shipping_address": "12 Example Street",
        "shipping_city": "Springfield",
        "shipping_postal_code": "10001",
        "shipping_country": "United States",
    }

    declined = client.post("/api/v1/orders", json={**checkout, "payment_result": "failure"})
    assert declined.status_code == 201
    assert declined.json()["payment_status"] == "failed"
    assert client.get("/api/v1/cart").json()["count"] == 2
    assert client.get("/api/v1/products/1").json()["stock"] == 12

    accepted = client.post("/api/v1/orders", json={**checkout, "payment_result": "success"})
    assert accepted.status_code == 201
    assert accepted.json()["payment_status"] == "paid"
    assert accepted.json()["total"] == "28.00"
    assert client.get("/api/v1/cart").json()["count"] == 0
    assert client.get("/api/v1/products/1").json()["stock"] == 10

    assert client.get(f"/api/v1/orders/{accepted.json()['id']}").status_code == 200
    assert client.get("/api/v1/orders/999").status_code == 404
    assert len(client.get("/api/v1/orders").json()) == 2


def test_customer_cannot_access_admin_and_admin_can_manage_store(client):
    register(client)
    assert client.get("/api/v1/admin/dashboard").status_code == 403
    assert client.post(
        "/api/v1/products",
        json={
            "title": "Customer product",
            "slug": "customer-product",
            "description": "This should not be allowed from a customer account.",
            "price": 10,
            "category_id": 1,
            "stock": 1,
        },
    ).status_code == 403

    admin_client(client)
    dashboard = client.get("/api/v1/admin/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["product_count"] == 2

    category = client.post(
        "/api/v1/categories",
        json={"name": "Travel", "slug": "travel", "description": "Useful things to take along."},
    )
    assert category.status_code == 201
    product = client.post(
        "/api/v1/products",
        json={
            "title": "Travel Pouch",
            "slug": "travel-pouch",
            "description": "A useful zip pouch for journeys and everyday carry.",
            "price": 19.5,
            "category_id": category.json()["id"],
            "stock": 5,
        },
    )
    assert product.status_code == 201
    product_id = product.json()["id"]
    updated = client.put(f"/api/v1/products/{product_id}", json={"stock": 7, "price": 22})
    assert updated.status_code == 200
    assert updated.json()["stock"] == 7
    assert updated.json()["price"] == "22.00"
    assert client.delete(f"/api/v1/products/{product_id}").status_code == 204


def test_customers_cannot_read_each_others_order_history(client):
    register(client, "first@example.com")
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1})
    order = client.post(
        "/api/v1/orders",
        json={
            "shipping_name": "First Customer",
            "shipping_address": "12 Example Street",
            "shipping_city": "Springfield",
            "shipping_postal_code": "10001",
            "shipping_country": "United States",
            "payment_result": "success",
        },
    ).json()

    client.post("/api/v1/auth/logout")
    register(client, "second@example.com")
    assert client.get(f"/api/v1/orders/{order['id']}").status_code == 404
    assert client.get("/api/v1/orders").json() == []
