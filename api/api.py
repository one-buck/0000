from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, KeyStatus
from schemas import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyPublic,
    APIKeyCreatedResponse,
    APIKeyVerifyRequest,
    APIKeyVerifyResponse,
    UsageStats,
    PaginatedKeys,
)
import services

router = APIRouter()


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "/keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
)
async def create_key(
    payload: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    key, raw_key = await services.create_key(db, payload)
    return APIKeyCreatedResponse(
        **APIKeyPublic.model_validate(key).model_dump(),
        raw_key=raw_key,
    )


@router.get(
    "/keys",
    response_model=PaginatedKeys,
    summary="List API keys for an owner",
)
async def list_keys(
    owner_id: str = Query(..., min_length=1),
    status_filter: Optional[KeyStatus] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    keys, total = await services.list_keys(db, owner_id, status_filter, limit, offset)
    return PaginatedKeys(
        items=[APIKeyPublic.model_validate(k) for k in keys],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/keys/{key_id}",
    response_model=APIKeyPublic,
    summary="Get a single API key by ID",
)
async def get_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    key = await services.get_key(db, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return APIKeyPublic.model_validate(key)


@router.patch(
    "/keys/{key_id}",
    response_model=APIKeyPublic,
    summary="Update key name, description, scopes, expiry, or status",
)
async def update_key(
    key_id: UUID,
    payload: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
):
    key = await services.update_key(db, key_id, payload)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return APIKeyPublic.model_validate(key)


@router.post(
    "/keys/{key_id}/revoke",
    response_model=APIKeyPublic,
    summary="Revoke a key immediately",
)
async def revoke_key(
    key_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    key = await services.revoke_key(db, key_id, ip_address=_client_ip(request))
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return APIKeyPublic.model_validate(key)


@router.post(
    "/keys/{key_id}/rotate",
    response_model=APIKeyCreatedResponse,
    summary="Rotate a key — invalidates the old secret, issues a new one",
)
async def rotate_key(
    key_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await services.rotate_key(db, key_id, ip_address=_client_ip(request))
    if not result:
        raise HTTPException(status_code=404, detail="Key not found")
    key, raw_key = result
    return APIKeyCreatedResponse(
        **APIKeyPublic.model_validate(key).model_dump(),
        raw_key=raw_key,
    )


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a key",
)
async def delete_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await services.delete_key(db, key_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Key not found")


@router.post(
    "/keys/verify",
    response_model=APIKeyVerifyResponse,
    summary="Validate a raw API key — hot path for gateways",
)
async def verify_key(
    payload: APIKeyVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await services.verify_key(db, payload.key, ip_address=_client_ip(request))
    return APIKeyVerifyResponse(**result)


@router.get(
    "/keys/{key_id}/usage",
    response_model=UsageStats,
    summary="Get usage stats and recent events for a key",
)
async def get_usage(
    key_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stats = await services.get_usage(db, key_id, limit=limit)
    if not stats:
        raise HTTPException(status_code=404, detail="Key not found")
    return UsageStats(**stats)