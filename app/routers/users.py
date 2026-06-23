from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional

from database import get_db, User, GroupMember, Group
from schemas import UserCreate, UserUpdate, UserResponse, GroupResponse
from utils import get_entity_or_404

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Phone number already registered.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 50,
    phone_number: Optional[str] = Query(None, description="Filter by phone number (exact match)"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)
    if phone_number:
        stmt = stmt.where(User.phone_number == phone_number)
    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_entity_or_404(db, User, user_id, "User not found")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, update_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await get_entity_or_404(db, User, user_id, "User not found")
    if update_data.username is not None:
        user.username = update_data.username
    if update_data.phone_number is not None:
        user.phone_number = update_data.phone_number
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Phone number already registered.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_entity_or_404(db, User, user_id, "User not found")
    await db.delete(user)
    try:
        await db.commit()
        return {"detail": "User deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/groups", response_model=List[GroupResponse])
async def get_user_groups(user_id: int, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, user_id, "User not found")
    stmt = (
        select(Group)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .where(GroupMember.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
