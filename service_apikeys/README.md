# service_apikeys

FastAPI service template.

## Features

* 

## Project Structure

```text
.
├── app
│   ├── routes
│   ├── config.py
│   ├── logger.py
│   ├── dependencies.py
│   ├── utils.py
│   └── main.py
├── tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```
### Folder & File Descriptions

| Path                  | Purpose                                                              |
|-----------------------|----------------------------------------------------------------------|
| `app/`                | Core application package containing configs, routes, and utilities   |
| `app/config.py`       | Centralized configuration using environment variables                |
| `app/logger.py`       | Logging setup with custom formatter and log level control            |
| `app/utils.py`        | Utility functions                                                    |
| `app/dependencies.py` | Shared dependencies for injection across routes/services             |
| `app/main.py`         | FastAPI entrypoint, lifespan events, and health check endpoint       |
| `app/routes/`         | API route definitions grouped by feature                             |
| `app/routes/items.py` | Example CRUD route for items                                         |
| `tests/`              | Unit and integration tests                                           |
| `Dockerfile`          | Container build instructions for the service                         |
| `docker-compose.yml`  | Compose setup for local development and service orchestration        |
| `requirements.txt`    | Python dependencies for the project                                  |
| `.env.example`        | Example environment configuration file                               |
| `.gitignore`          | Files and directories excluded from version control                  |
| `README.md`           | Project documentation and usage guide                                |

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

