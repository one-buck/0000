'''
======================================================================
File: entities.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

import enum
import uuid

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

from app.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass


class KeyStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class EventType(str, enum.Enum):
    created = "created"
    verified = "verified"
    revoked = "revoked"
    rotated = "rotated"
    updated = "updated"
    deleted = "deleted"


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(String(128), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    key_hash = Column(String(64), nullable=False, unique=True)
    prefix = Column(String(16), nullable=False)
    environment = Column(String(32), nullable=False, default="production")
    status = Column(SAEnum(KeyStatus), nullable=False, default=KeyStatus.active)
    scopes = Column(ARRAY(String), nullable=False, default=list)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_api_keys_key_hash", "key_hash"),
        Index("ix_api_keys_owner_status", "owner_id", "status"),
    )


class APIKeyEvent(Base):
    __tablename__ = "api_key_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id = Column(PGUUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(SAEnum(EventType), nullable=False)
    ip_address = Column(String(64), nullable=True)
    metadata_ = Column("metadata", Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_api_key_events_key_id", "key_id"),
        Index("ix_api_key_events_created_at", "created_at"),
    )


async def init_db() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
