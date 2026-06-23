from fastapi import APIRouter, Query
from typing import Optional

import search

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/messages")
async def search_messages(
    q: str = Query(..., min_length=1, description="Full-text search query"),
    sender_id: Optional[int] = Query(None, description="Filter by sender"),
    receiver_id: Optional[int] = Query(None, description="Filter by receiver or group ID"),
    skip: int = 0,
    limit: int = 50,
):
    """
    Full-text search over message content.
    Supports fuzzy matching. Excludes soft-deleted messages.
    Optionally filter by sender_id or receiver_id (works for both DMs and group IDs).
    """
    return await search.search_messages(
        query=q,
        sender_id=sender_id,
        receiver_id=receiver_id,
        skip=skip,
        limit=limit,
    )


@router.get("/groups")
async def search_groups(
    q: str = Query(..., min_length=1, description="Full-text search query"),
    skip: int = 0,
    limit: int = 50,
):
    """Full-text search over group names. Supports fuzzy matching."""
    return await search.search_groups(query=q, skip=skip, limit=limit)
