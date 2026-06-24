import hashlib
import secrets
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from database import APIKey, APIKeyEvent, KeyStatus, EventType
from schemas import APIKeyCreate, APIKeyUpdate
from config import settings


def _generate_raw_key(environment: str) -> tuple[str, str, str]:
    prefix_map = {
        "production": settings.key_prefix_live,
        "staging": settings.key_prefix_test,
        "development": settings.key_prefix_dev,
    }
    prefix = prefix_map.get(environment, settings.key_prefix_live)
    secret = secrets.token_urlsafe(settings.default_key_length)
    raw_key = f"{prefix}_{secret}"
    return raw_key, prefix, secret


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _is_expired(key: APIKey) -> bool:
    if key.expires_at is None:
        return False
    return datetime.now(timezone.utc) > key.expires_at.replace(tzinfo=timezone.utc)


async def _write_event(
    db: AsyncSession,
    key_id: UUID,
    event_type: EventType,
    ip_address: Optional[str] = None,
    success: bool = True,
    metadata: Optional[dict] = None,
):
    event = APIKeyEvent(
        key_id=key_id,
        event_type=event_type,
        ip_address=ip_address,
        success=success,
        metadata_=json.dumps(metadata) if metadata else None,
    )
    db.add(event)


async def create_key(db: AsyncSession, payload: APIKeyCreate) -> tuple[APIKey, str]:
    raw_key, prefix, _ = _generate_raw_key(payload.environment)
    key_hash = _hash_key(raw_key)

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
    db.add(api_key)
    await db.flush()
    await _write_event(db, api_key.id, EventType.created)
    return api_key, raw_key


async def list_keys(
    db: AsyncSession,
    owner_id: str,
    status: Optional[KeyStatus] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[APIKey], int]:
    query = select(APIKey).where(APIKey.owner_id == owner_id)
    count_query = select(func.count()).select_from(APIKey).where(APIKey.owner_id == owner_id)

    if status:
        query = query.where(APIKey.status == status)
        count_query = count_query.where(APIKey.status == status)

    total = (await db.execute(count_query)).scalar_one()
    keys = (await db.execute(query.order_by(APIKey.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return list(keys), total


async def get_key(db: AsyncSession, key_id: UUID) -> Optional[APIKey]:
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    return result.scalar_one_or_none()


async def update_key(db: AsyncSession, key_id: UUID, payload: APIKeyUpdate) -> Optional[APIKey]:
    key = await get_key(db, key_id)
    if not key:
        return None

    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(key, field, value)

    await _write_event(db, key_id, EventType.updated, metadata={"fields": list(changes.keys())})
    return key


async def revoke_key(db: AsyncSession, key_id: UUID, ip_address: Optional[str] = None) -> Optional[APIKey]:
    key = await get_key(db, key_id)
    if not key:
        return None

    key.status = KeyStatus.revoked
    await _write_event(db, key_id, EventType.revoked, ip_address=ip_address)
    return key


async def delete_key(db: AsyncSession, key_id: UUID) -> bool:
    key = await get_key(db, key_id)
    if not key:
        return False

    await _write_event(db, key_id, EventType.deleted)
    await db.delete(key)
    return True


async def verify_key(
    db: AsyncSession, raw_key: str, ip_address: Optional[str] = None
) -> dict:
    key_hash = _hash_key(raw_key)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    key = result.scalar_one_or_none()

    if not key:
        return {"valid": False, "reason": "key_not_found"}

    if key.status == KeyStatus.revoked:
        await _write_event(db, key.id, EventType.verified, ip_address=ip_address, success=False)
        return {"valid": False, "reason": "key_revoked"}

    if _is_expired(key):
        key.status = KeyStatus.expired
        await _write_event(db, key.id, EventType.verified, ip_address=ip_address, success=False)
        return {"valid": False, "reason": "key_expired"}

    key.last_used_at = datetime.now(timezone.utc)
    key.usage_count += 1
    await _write_event(db, key.id, EventType.verified, ip_address=ip_address, success=True)

    return {
        "valid": True,
        "key_id": key.id,
        "owner_id": key.owner_id,
        "scopes": key.scopes,
        "environment": key.environment,
    }


async def get_usage(db: AsyncSession, key_id: UUID, limit: int = 50) -> Optional[dict]:
    key = await get_key(db, key_id)
    if not key:
        return None

    events_result = await db.execute(
        select(APIKeyEvent)
        .where(APIKeyEvent.key_id == key_id)
        .order_by(APIKeyEvent.created_at.desc())
        .limit(limit)
    )
    events = events_result.scalars().all()

    return {
        "key_id": key.id,
        "usage_count": key.usage_count,
        "last_used_at": key.last_used_at,
        "recent_events": events,
    }


async def rotate_key(db: AsyncSession, key_id: UUID, ip_address: Optional[str] = None) -> Optional[tuple[APIKey, str]]:
    key = await get_key(db, key_id)
    if not key:
        return None

    raw_key, prefix, _ = _generate_raw_key(key.environment)
    key.key_hash = _hash_key(raw_key)
    key.prefix = f"{prefix}_****"
    key.usage_count = 0
    key.last_used_at = None

    await _write_event(db, key_id, EventType.rotated, ip_address=ip_address)
    return key, raw_key