from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from config import APP_DIR, JWT_SECRET
from database import Base, SessionLocal, engine
from models import Category  # noqa: F401 - ensures all models are registered before create_all
from routers import admin, auth, cart, categories, orders, products
from services.seed import seed_sample_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is missing. Copy .env.example to .env and set JWT_SECRET before starting the app.")
    if os.getenv("TESTING") != "1":
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_sample_data(db)
    yield


app = FastAPI(
    title="Northstar Supply Store API",
    description="A local-first sample shop with customer accounts, admin inventory, and simulated checkout.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
for api_router in (auth.router, products.router, categories.router, cart.router, orders.router, admin.router):
    app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def storefront() -> FileResponse:
    return FileResponse(APP_DIR / "static" / "index.html")


@app.get("/{full_path:path}", include_in_schema=False)
def not_found(full_path: str) -> FileResponse:
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "static/")):
        raise HTTPException(status_code=404, detail="Not found.")
    return FileResponse(APP_DIR / "static" / "index.html")

