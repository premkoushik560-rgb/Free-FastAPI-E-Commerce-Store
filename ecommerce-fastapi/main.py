
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
import models
from routers import auth, products, categories, cart, orders, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="E-Commerce Backend API",
    description="Free e-commerce REST API using FastAPI and SQLite",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/")
def home():
    return {
        "message": "Welcome to the E-Commerce Backend API!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
