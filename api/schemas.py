from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import datetime
from database import KeyStatus, EventType


class APIKeyCreate(BaseModel):
    owner_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    environment: str = Field(default="production", pattern="^(production|staging|development)$")
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
    id: UUID4
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
    key_id: Optional[UUID4] = None
    scopes: Optional[List[str]] = None
    environment: Optional[str] = None
    reason: Optional[str] = None


class APIKeyEventPublic(BaseModel):
    id: UUID4
    key_id: UUID4
    event_type: EventType
    ip_address: Optional[str]
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageStats(BaseModel):
    key_id: UUID4
    usage_count: int
    last_used_at: Optional[datetime]
    recent_events: List[APIKeyEventPublic]


class PaginatedKeys(BaseModel):
    items: List[APIKeyPublic]
    total: int
    limit: int
    offset: int