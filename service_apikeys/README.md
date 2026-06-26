# API Key Management Service

A standalone FastAPI service for API key lifecycle management: create, verify, revoke, and rotate.

## Features

- **Create** API keys with environment-specific prefixes (`sk_live_`, `sk_test_`, `sk_dev_`)
- **Verify** keys on the hot path for API gateways
- **Revoke** keys immediately
- **Rotate** keys to issue new secrets without changing the key ID
- **Track** usage with event logging (created, verified, revoked, rotated, updated, deleted)
- **List** and **filter** keys by owner and status with pagination

## Quick Start

### Using Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Using Python (local)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://apikey_user:apikey_pass@localhost:5432/apikey_db"

# Run the server
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/keys` | Create a new API key |
| `GET` | `/v1/keys` | List API keys by owner |
| `GET` | `/v1/keys/{key_id}` | Get a single key |
| `PATCH` | `/v1/keys/{key_id}` | Update key metadata |
| `POST` | `/v1/keys/{key_id}/revoke` | Revoke a key |
| `POST` | `/v1/keys/{key_id}/rotate` | Rotate a key |
| `DELETE` | `/v1/keys/{key_id}` | Delete a key |
| `POST` | `/v1/keys/verify` | Verify a raw key |
| `GET` | `/v1/keys/{key_id}/usage` | Get usage statistics |
| `GET` | `/health` | Health check |

## Example Usage

### Create a Key

```bash
curl -X POST http://localhost:8000/v1/keys \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "user-123",
    "name": "Production API Key",
    "environment": "production",
    "scopes": ["read", "write"]
  }'
```

**Note:** The `raw_key` is only returned once at creation time. Store it securely!

### Verify a Key

```bash
curl -X POST http://localhost:8000/v1/keys/verify \
  -H "Content-Type: application/json" \
  -d '{"key": "sk_live_abc123..."}'
```

### List Keys

```bash
curl "http://localhost:8000/v1/keys?owner_id=user-123&limit=10&offset=0"
```

### Revoke a Key

```bash
curl -X POST http://localhost:8000/v1/keys/{key_id}/revoke
```

### Rotate a Key

```bash
curl -X POST http://localhost:8000/v1/keys/{key_id}/rotate
```

## Project Structure

```
app/
├── models/          # SQLAlchemy entities and Pydantic schemas
├── repositories/    # Database query layer
├── routes/          # API endpoints
├── services/        # Business logic
├── tests/           # Test suite
├── config.py        # Application settings
├── dependencies.py  # FastAPI dependencies
├── logger.py        # Logging configuration
├── main.py          # Application entry point
└── utils.py         # Utility functions
```

## Environment Variables

See `.env.example` for all available configuration options.

