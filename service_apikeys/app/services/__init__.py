'''
======================================================================
File: __init__.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import APIKey, EventType, KeyStatus
from app.models.schemas import APIKeyCreate, APIKeyUpdate
from app.repositories import (
    add_event,
    add_key,
    delete_key_record,
    get_events_by_key_id,
    get_key_by_hash,
    get_key_by_id,
    list_keys_by_owner,
    update_key_fields,
)
from app.utils import generate_raw_key, hash_key, is_expired


async def create_key(
    db: AsyncSession, payload: APIKeyCreate
) -> tuple[APIKey, str]:
    """Create a new API key and return the entity with the raw key."""
    raw_key, prefix, _ = generate_raw_key(payload.environment)
    key_hash = hash_key(raw_key)

    api_key = APIKey(
        owner_id=payload.owner_id,
        name=payload.name,
        description=payload.description,
        key_hash=key_hash,
        prefix=f"{prefix}_****",
        environment=payload.environment,
        scopes=payload.scopes,
        expires_at=payload.expires_at,
    )
    await add_key(db, api_key)
    await add_event(db, api_key.id, EventType.created)
    return api_key, raw_key


async def list_keys(
    db: AsyncSession,
    owner_id: str,
    status: Optional[KeyStatus] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[APIKey], int]:
    """List API keys belonging to an owner."""
    return await list_keys_by_owner(db, owner_id, status, limit, offset)


async def get_key(db: AsyncSession, key_id: UUID) -> Optional[APIKey]:
    """Retrieve a single API key by ID."""
    return await get_key_by_id(db, key_id)


async def update_key(
    db: AsyncSession, key_id: UUID, payload: APIKeyUpdate
) -> Optional[APIKey]:
    """Update mutable fields on an API key."""
    key = await get_key_by_id(db, key_id)
    if not key:
        return None

    changes = payload.model_dump(exclude_none=True)
    await update_key_fields(db, key, changes)
    await add_event(
        db, key_id, EventType.updated, metadata={"fields": list(changes.keys())}
    )
    return key


async def revoke_key(
    db: AsyncSession, key_id: UUID, ip_address: Optional[str] = None
) -> Optional[APIKey]:
    """Revoke an API key immediately."""
    key = await get_key_by_id(db, key_id)
    if not key:
        return None

    await update_key_fields(db, key, {"status": KeyStatus.revoked})
    await add_event(db, key_id, EventType.revoked, ip_address=ip_address)
    return key


async def delete_key(db: AsyncSession, key_id: UUID) -> bool:
    """Permanently delete an API key and its events (via cascade)."""
    key = await get_key_by_id(db, key_id)
    if not key:
        return False

    await add_event(db, key_id, EventType.deleted)
    await delete_key_record(db, key)
    return True


async def verify_key(
    db: AsyncSession, raw_key: str, ip_address: Optional[str] = None
) -> dict:
    """Verify a raw API key and return validation result.

    This is the hot path called by API gateways.
    """
    key_hash = hash_key(raw_key)
    key = await get_key_by_hash(db, key_hash)

    if not key:
        return {"valid": False, "reason": "key_not_found"}

    if key.status == KeyStatus.revoked:
        await add_event(
            db, key.id, EventType.verified, ip_address=ip_address, success=False
        )
        return {"valid": False, "reason": "key_revoked"}

    if is_expired(key):
        await update_key_fields(db, key, {"status": KeyStatus.expired})
        await add_event(
            db, key.id, EventType.verified, ip_address=ip_address, success=False
        )
        return {"valid": False, "reason": "key_expired"}

    await update_key_fields(
        db,
        key,
        {
            "last_used_at": datetime.now(timezone.utc),
            "usage_count": key.usage_count + 1,
        },
    )
    await add_event(db, key.id, EventType.verified, ip_address=ip_address, success=True)

    return {
        "valid": True,
        "key_id": key.id,
        "owner_id": key.owner_id,
        "scopes": key.scopes,
        "environment": key.environment,
    }


async def get_usage(
    db: AsyncSession, key_id: UUID, limit: int = 50
) -> Optional[dict]:
    """Get usage statistics and recent events for a key."""
    key = await get_key_by_id(db, key_id)
    if not key:
        return None

    events = await get_events_by_key_id(db, key_id, limit)

    return {
        "key_id": key.id,
        "usage_count": key.usage_count,
        "last_used_at": key.last_used_at,
        "recent_events": events,
    }


async def rotate_key(
    db: AsyncSession, key_id: UUID, ip_address: Optional[str] = None
) -> Optional[tuple[APIKey, str]]:
    """Rotate an API key — invalidates the old secret, issues a new one."""
    key = await get_key_by_id(db, key_id)
    if not key:
        return None

    raw_key, prefix, _ = generate_raw_key(key.environment)
    await update_key_fields(
        db,
        key,
        {
            "key_hash": hash_key(raw_key),
            "prefix": f"{prefix}_****",
            "usage_count": 0,
            "last_used_at": None,
        },
    )
    await add_event(db, key_id, EventType.rotated, ip_address=ip_address)
    return key, raw_key
