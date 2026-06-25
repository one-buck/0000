'''
======================================================================
File: main.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.logger import logger
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME}")
    # Startup logic here (db init, etc.)
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    # Cleanup here


app = FastAPI(
    title=settings.SERVICE_NAME,
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}
