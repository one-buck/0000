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
RUN pip install uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"
""",

    "docker-compose.yml": """
services:
  app:
    build: .
    container_name: ${SERVICE_NAME}
    env_file:
      - .env
    ports:
      - "${SERVICE_PORT}:${SERVICE_PORT}"
    restart: unless-stopped
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
venv/

# Environment files
.env

# IDEs
.vscode/
.idea/

# Logs
*.log

# Added files
.gitignore
""",

    "README.md": """# {{SERVICE_NAME}}

FastAPI service template.

## Features

* 

## Project Structure

```text
.
├─── app
│   │
│   ├─── models
│   │   ├─── entities.py
│   │   ├─── schemas.py
│   │   └─── __init__.py
│   │
│   ├─── repositories
│   │   └─── __init__.py
│   │
│   ├─── routes
│   │   ├─── items.py
│   │   └─── __init__.py
│   │       
│   ├─── services
│   │   └─── __init__.py
│   │
│   ├─── tests
│   │   └─── __init__.py
│   │
│   ├─── config.py
│   ├─── dependencies.py
│   ├─── logger.py
│   ├─── main.py
│   ├─── utils.py
│   └─── __init__.py
│
├─── .env.example
├─── .gitignore
├─── docker-compose.yml
├─── Dockerfile
├─── requirements.txt
└─── README.md
```
### Folder & File Descriptions

| Path                     | Purpose                                                             |
|--------------------------|---------------------------------------------------------------------|
| `app/`                   | CCore application package containing configs, routes, and utilities |
| `app/config.py`          | Centralized configuration using environment variables               |
| `app/dependencies.py`    | Shared dependencies for injection across routes/services            |
| `app/logger.py`          | Logging configuration and custom logger setup                       |
| `app/main.py`            | FastAPI entrypoint, lifespan events, and health check endpoint      |
| `app/utils.py`           | Common utility and helper functions                                 |
| `models/`                | Domain models, entities, and API schemas                            |
| `models/entities.py`     | Database/domain entity definitions                                  |
| `models/schemas.py`      | Pydantic request and response schemas                               |
| `repositories/`          | Data access layer responsible for interacting with data sources     |
| `routes/`                | API endpoint definitions grouped by feature                         |
| `routes/items.py`        | Example CRUD route for items                                        |
| `services/`              | Business logic layer that orchestrates repositories and domain operations |
| `tests/`                 | Unit, integration, and API tests                                    |
| `Dockerfile`             | Docker image build instructions                                     |
| `docker-compose.yml`     | Local development and multi-container orchestration configuration   |
| `requirements.txt`       | Python package dependencies                                         |
| `.env.example`           | Example environment variables file                                  |
| `.gitignore`             | Files and directories excluded from version control                 |
| `README.md`              | Project documentation, setup instructions, and usage guide          |                               |

## Configuration

```bash
cp .env.example .env
```

## Running With Docker Compose

```bash
docker compose up --build
```

## Health Check

```http
GET /health
```

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
    SERVICE_PORT: str = "8000"
    SERVICE_URL: str = "localhost"
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

logger = get_logger(__name__)
""",

    "app/utils.py": """from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)

""",

    "app/dependencies.py": """from app.config import Settings
from app.logger import logger

""",

    "app/main.py": """from contextlib import asynccontextmanager
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
""",

    # ── app/routes/ ──
    "app/routes/__init__.py": """from fastapi import APIRouter

from app.routes.items import router as items_router


router = APIRouter()

router.include_router(items_router, prefix="/items", tags=["items"])

""",

    "app/routes/items.py": """from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ItemCreate, ItemResponse


router = APIRouter()

@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(data: ItemCreate):
    return {
    "id": 0,
    "name": data.name,
    "description": data.description,
    "created_at": "2024-07-15T10:30:00"
}


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return {
    "id": item_id,
    "name": "Wireless Mouse",
    "description": "A sleek ergonomic mouse with Bluetooth support",
    "created_at": "2024-07-15T10:30:00"
}

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

    "app/models/entities.py": "",

    # ── app/services/ ──
    "app/services/__init__.py": "",

    # ── app/repositories/ ──
    "app/repositories/__init__.py": "",

    # ── tests/ ──
    "tests/__init__.py": "",
}


def make_header(filename: str) -> str:
    """Generate file header for .py files."""
    # format = "%Y-%m-%d %H:%M:%S"
    format = "%Y-%m-%d"
    now = datetime.now().strftime(format)
    separator = "=" * 70
    return f"'''\n{separator}\nFile: {filename}\nAuthor: {AUTHOR}\nCreated: {now}\n{separator}\n'''\n\n"

def create_service(output_dir: str, service_name: str) -> None:
    out_path = Path(output_dir).resolve()
    service_dir = out_path / service_name

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

        # Add header only to .py files with/out content 
        # if file_path.suffix == ".py" and content.strip():
        if file_path.suffix == ".py" :
            full_content = make_header(filename) + content.lstrip("\n")
        else:
            full_content = content.lstrip("\n") if content else ""
        
        if filename == "README.md":
            full_content = full_content.replace(
                "{{SERVICE_NAME}}", service_name
            )
        file_path.write_text(full_content, encoding="utf-8")

    # Write dynamic .env.example
    env_content = f"""SERVICE_NAME={service_name}
SERVICE_PORT="8000"
SERVICE_URL="localhost"
LOG_LEVEL=INFO
"""
    (service_dir / ".env.example").write_text(env_content.strip(), encoding="utf-8")

    # Done
    print(f"\n{GREEN}✓ Service created successfully!{NC}\n")
    print("Next steps:")
    print(f"cd {service_dir}")
    print("cp .env.example .env")
    print("# Edit .env with your settings")
    print("docker compose up --build")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <output-dir> <service-name>")
        print(f"Example: python {sys.argv[0]} ./services users")
        sys.exit(1)

    create_service(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()