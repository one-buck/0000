'''
======================================================================
File: main.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.entities import init_db
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="API Key Management Service",
    description=(
        "Standalone service for API key lifecycle management: "
        "create, verify, revoke, rotate."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/v1")


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": settings.SERVICE_NAME}