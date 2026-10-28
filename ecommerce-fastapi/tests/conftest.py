from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-production")
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.security import hash_password
from database import Base, get_db
from main import app
from models import Category, Product, User


@pytest.fixture
def client(tmp_path):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)

    with TestingSession() as db:
        everyday = Category(name="Everyday Carry", slug="everyday-carry", description="Daily essentials.")
        studio = Category(name="Desk & Studio", slug="desk-studio", description="Tools for work.")
        db.add_all([everyday, studio])
        db.flush()
        db.add_all(
            [
                Product(
                    title="Pocket Journal",
                    slug="pocket-journal",
                    description="A durable small notebook for everyday notes.",
                    price=14,
                    category_id=everyday.id,
                    image_url="/static/images/journal.svg",
                    stock=12,
                ),
                Product(
                    title="Desk Tray",
                    slug="desk-tray",
                    description="A small tray for the useful things on your desk.",
                    price=28,
                    category_id=studio.id,
                    image_url="/static/images/desk.svg",
                    stock=2,
                ),
            ]
        )
        db.add(
            User(
                name="Store Admin",
                email="admin@example.com",
                password_hash=hash_password("test-admin-password"),
                role="admin",
            )
        )
        db.commit()

    def override_get_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def register(client: TestClient, email: str = "customer@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Sample Customer", "email": email, "password": "correct-horse-1"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def admin_client(client: TestClient) -> TestClient:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "test-admin-password"},
    )
    assert response.status_code == 200, response.text
    return client

