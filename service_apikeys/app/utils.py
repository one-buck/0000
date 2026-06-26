'''
======================================================================
File: utils.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.models.entities import APIKey


def generate_raw_key(environment: str) -> tuple[str, str, str]:
    """Generate a raw API key with appropriate prefix.

    Returns:
        Tuple of (raw_key, prefix, secret)
    """
    prefix_map = {
        "production": settings.KEY_PREFIX_LIVE,
        "staging": settings.KEY_PREFIX_TEST,
        "development": settings.KEY_PREFIX_DEV,
    }
    prefix = prefix_map.get(environment, settings.KEY_PREFIX_LIVE)
    secret = secrets.token_urlsafe(settings.DEFAULT_KEY_LENGTH)
    raw_key = f"{prefix}_{secret}"
    return raw_key, prefix, secret


def hash_key(raw_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def is_expired(key: APIKey) -> bool:
    """Check if a key has expired based on its expires_at timestamp."""
    if key.expires_at is None:
        return False
    return datetime.now(timezone.utc) > key.expires_at.replace(tzinfo=timezone.utc)


def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request, handling X-Forwarded-For header."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
