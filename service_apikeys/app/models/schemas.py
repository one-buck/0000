'''
======================================================================
File: schemas.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.entities import EventType, KeyStatus



class APIKeyCreate(BaseModel):
    owner_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    environment: str = Field(
        default="production",
        pattern="^(production|staging|development)$",
    )
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    status: Optional[KeyStatus] = None


class APIKeyVerifyRequest(BaseModel):
    key: str = Field(..., min_length=10)


class APIKeyPublic(BaseModel):
    id: UUID
    owner_id: str
    name: str
    description: Optional[str]
    prefix: str
    environment: str
    status: KeyStatus
    scopes: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyPublic):
    raw_key: str = Field(..., description="Shown only once at creation time")


class APIKeyVerifyResponse(BaseModel):
    valid: bool
    owner_id: Optional[str] = None
    key_id: Optional[UUID] = None
    scopes: Optional[List[str]] = None
    environment: Optional[str] = None
    reason: Optional[str] = None


class APIKeyEventPublic(BaseModel):
    id: UUID
    key_id: UUID
    event_type: EventType
    ip_address: Optional[str]
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageStats(BaseModel):
    key_id: UUID
    usage_count: int
    last_used_at: Optional[datetime]
    recent_events: List[APIKeyEventPublic]


class PaginatedKeys(BaseModel):
    items: List[APIKeyPublic]
    total: int
    limit: int
    offset: int
