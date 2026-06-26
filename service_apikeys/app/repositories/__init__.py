'''
======================================================================
File: __init__.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import APIKey, APIKeyEvent, EventType, KeyStatus



async def get_key_by_id(db: AsyncSession, key_id: UUID) -> Optional[APIKey]:
    """Fetch a single API key by its ID."""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    return result.scalar_one_or_none()


async def get_key_by_hash(db: AsyncSession, key_hash: str) -> Optional[APIKey]:
    """Fetch a single API key by its hashed value."""
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    return result.scalar_one_or_none()


async def list_keys_by_owner(
    db: AsyncSession,
    owner_id: str,
    status: Optional[KeyStatus] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[APIKey], int]:
    """List API keys for a given owner with optional status filter."""
    query = select(APIKey).where(APIKey.owner_id == owner_id)
    count_query = (
        select(func.count())
        .select_from(APIKey)
        .where(APIKey.owner_id == owner_id)
    )

    if status:
        query = query.where(APIKey.status == status)
        count_query = count_query.where(APIKey.status == status)

    total = (await db.execute(count_query)).scalar_one()
    keys = (
        await db.execute(
            query.order_by(APIKey.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()

    return list(keys), total


async def add_key(db: AsyncSession, key: APIKey) -> APIKey:
    """Add a new API key to the database and flush."""
    db.add(key)
    await db.flush()
    return key


async def update_key_fields(
    db: AsyncSession,
    key: APIKey,
    fields: dict,
) -> APIKey:
    """Update specific fields on an existing API key."""
    for field, value in fields.items():
        setattr(key, field, value)
    return key


async def delete_key_record(db: AsyncSession, key: APIKey) -> None:
    """Delete an API key record from the database."""
    await db.delete(key)


async def get_events_by_key_id(
    db: AsyncSession,
    key_id: UUID,
    limit: int = 50,
) -> list[APIKeyEvent]:
    """Fetch recent events for a specific API key."""
    result = await db.execute(
        select(APIKeyEvent)
        .where(APIKeyEvent.key_id == key_id)
        .order_by(APIKeyEvent.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def add_event(
    db: AsyncSession,
    key_id: UUID,
    event_type: EventType,
    ip_address: Optional[str] = None,
    success: bool = True,
    metadata: Optional[dict] = None,
) -> APIKeyEvent:
    """Record an event for an API key."""
    event = APIKeyEvent(
        key_id=key_id,
        event_type=event_type,
        ip_address=ip_address,
        success=success,
        metadata_=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
    return event
