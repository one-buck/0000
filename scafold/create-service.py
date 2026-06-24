"""
create_service.py - Scaffold a new FastAPI microservice
Usage: python create_service.py <output-dir> <service-name>
"""

import sys
from datetime import datetime
from pathlib import Path

# ─── Config ───
AUTHOR = "Z Name, " 

# ─── Colors ───
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
NC = "\033[0m"

# ─── Templates ───
TEMPLATES: dict[str, str] = {
    # ── Root files ──
    "Dockerfile": """FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",

    "requirements.txt": """fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic-settings==2.5.0
""",

    # ── app/ ──
    "app/__init__.py": "",

    "app/config.py": """from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "service"
    DATABASE_URL: str
    REDIS_URL: str | None = None
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
""",

    "app/logger.py": """import logging
import sys

from app.config import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    return logger
""",

    "app/utils.py": """from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)

""",

    "app/dependencies.py": """from functools import lru_cache

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    from app.config import settings
    return settings
""",

    "app/main.py": """from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logger import get_logger
from app.routes import router

logger = get_logger(__name__)


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
""",

    # ── app/routes/ ──
    "app/routes/__init__.py": """from fastapi import APIRouter

router = APIRouter()

# Add your route modules below:
# from app.routes.items import router as items_router
# router.include_router(items_router, prefix="/items", tags=["items"])
""",

    "app/routes/items.py": """from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ItemCreate, ItemResponse
from app.services.item_service import ItemService, get_item_service

router = APIRouter()


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    data: ItemCreate,
    svc: ItemService = Depends(get_item_service),
):
    return await svc.create(data)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    svc: ItemService = Depends(get_item_service),
):
    item = await svc.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
""",

    # ── app/models/ ──
    "app/models/__init__.py": "",

    "app/models/schemas.py": """from datetime import datetime

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
""",

    "app/models/entities.py": """from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
""",

    # ── app/services/ ──
    "app/services/__init__.py": "",

    "app/services/item_service.py": """from fastapi import Depends

from app.logger import get_logger
from app.models.schemas import ItemCreate, ItemResponse
from app.repositories.item_repo import ItemRepo, get_item_repo

logger = get_logger(__name__)


class ItemService:
    def __init__(self, repo: ItemRepo):
        self.repo = repo

    async def create(self, data: ItemCreate) -> ItemResponse:
        logger.info(f"Creating item: {data.name}")
        item = await self.repo.insert(data.model_dump())
        return ItemResponse.model_validate(item)

    async def get(self, item_id: int) -> ItemResponse | None:
        item = await self.repo.find_by_id(item_id)
        if item:
            return ItemResponse.model_validate(item)
        return None


def get_item_service(repo: ItemRepo = Depends(get_item_repo)) -> ItemService:
    return ItemService(repo=repo)
""",

    # ── app/repositories/ ──
    "app/repositories/__init__.py": "",

    "app/repositories/item_repo.py": """from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.entities import Base, Item

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class ItemRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert(self, data: dict) -> Item:
        item = Item(**data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def find_by_id(self, item_id: int) -> Item | None:
        result = await self.session.execute(select(Item).where(Item.id == item_id))
        return result.scalar_one_or_none()


async def get_item_repo() -> ItemRepo:
    async with async_session() as session:
        yield ItemRepo(session=session)
""",

    # ── tests/ ──
    "tests/__init__.py": "",

    "tests/conftest.py": """import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
""",

    "tests/test_items.py": """import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
""",
}


def make_header(filename: str) -> str:
    """Generate file header for .py files."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    separator = "=" * 70
    return f"'''\n{separator}\nFile: {filename}\nAuthor: {AUTHOR}\nCreated: {now}\n{separator}\n'''\n\n"


def create_service(output_dir: str, service_name: str) -> None:
    out_path = Path(output_dir).resolve()
    service_dir = out_path / service_name
    module_name = service_name.replace("-", "_")

    # Validate output dir
    if not out_path.exists():
        print(f"{RED}❌ Output directory does not exist: {out_path}{NC}")
        sys.exit(1)

    if service_dir.exists():
        print(f"{RED}❌ Service already exists: {service_dir}{NC}")
        sys.exit(1)

    print(f"{CYAN}Creating service: {service_name}{NC}")
    print(f"{CYAN}Location: {service_dir}{NC}")

    # Create directories
    for subdir in ["app/routes", "app/models", "app/services", "app/repositories", "tests"]:
        (service_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Write templates
    for rel_path, content in TEMPLATES.items():
        file_path = service_dir / rel_path
        filename = file_path.name

        # Add header only to .py files with content
        if file_path.suffix == ".py" and content.strip():
            full_content = make_header(filename) + content.lstrip("\n")
        else:
            full_content = content.lstrip("\n") if content else ""

        file_path.write_text(full_content, encoding="utf-8")

    # Write dynamic .env.example
    env_content = f"""SERVICE_NAME={service_name}
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/{module_name}_db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
"""
    (service_dir / ".env.example").write_text(env_content.strip(), encoding="utf-8")

    # Done
    print(f"\n{GREEN}✓ Service created successfully!{NC}\n")
    print("Next steps:")
    print(f"  1. cd {service_dir}")
    print("  2. cp .env.example .env")
    print("  3. Edit .env with your settings")
    print(f"  4. docker build -t {service_name} .")
    print(f"  5. docker run -p 8000:8000 --env-file .env {service_name}")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <output-dir> <service-name>")
        print(f"Example: python {sys.argv[0]} ./services users")
        sys.exit(1)

    create_service(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()