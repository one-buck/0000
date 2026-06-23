from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from database import get_db, User, UserConnection
from schemas import ConnectionUpsert, ConnectionResponse
from utils import get_entity_or_404

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.put("/{user_id}", response_model=ConnectionResponse)
async def upsert_connection(user_id: int, data: ConnectionUpsert, db: AsyncSession = Depends(get_db)):
    """Register or update a user's active connection (e.g. on WebSocket connect)."""
    await get_entity_or_404(db, User, user_id, "User not found")
    conn = await db.get(UserConnection, user_id)
    if conn:
        conn.server_id = data.server_id
        conn.connection_id = data.connection_id
        conn.device_type = data.device_type
    else:
        conn = UserConnection(user_id=user_id, **data.model_dump())
        db.add(conn)
    try:
        await db.commit()
        await db.refresh(conn)
        return conn
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=ConnectionResponse)
async def get_connection(user_id: int, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, user_id, "User not found")
    conn = await db.get(UserConnection, user_id)
    if not conn:
        raise HTTPException(status_code=404, detail="No active connection for this user")
    return conn


@router.delete("/{user_id}")
async def delete_connection(user_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a connection record (e.g. on WebSocket disconnect)."""
    await get_entity_or_404(db, User, user_id, "User not found")
    conn = await db.get(UserConnection, user_id)
    if not conn:
        raise HTTPException(status_code=404, detail="No active connection for this user")
    await db.delete(conn)
    try:
        await db.commit()
        return {"detail": "Connection removed"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ConnectionResponse])
async def list_connections(server_id: str = None, db: AsyncSession = Depends(get_db)):
    """List all active connections, optionally filtered by server."""
    stmt = select(UserConnection)
    if server_id:
        stmt = stmt.where(UserConnection.server_id == server_id)
    result = await db.execute(stmt)
    return result.scalars().all()
