from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from database import get_db, User, Group, GroupMember
from schemas import GroupCreate, GroupUpdate, GroupResponse, MemberResponse
from utils import get_entity_or_404

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/", response_model=GroupResponse, status_code=201)
async def create_group(group: GroupCreate, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, group.created_by, "Creator user not found")
    db_group = Group(name=group.name, created_by=group.created_by)
    db.add(db_group)
    await db.flush()
    db.add(GroupMember(group_id=db_group.id, user_id=group.created_by, role="admin"))
    try:
        await db.commit()
        await db.refresh(db_group)
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[GroupResponse])
async def get_groups(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    return await get_entity_or_404(db, Group, group_id, "Group not found")


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, update_data: GroupUpdate, db: AsyncSession = Depends(get_db)):
    group = await get_entity_or_404(db, Group, group_id, "Group not found")
    group.name = update_data.name
    try:
        await db.commit()
        await db.refresh(group)
        return group
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await get_entity_or_404(db, Group, group_id, "Group not found")
    await db.delete(group)
    try:
        await db.commit()
        return {"detail": "Group deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{group_id}/members/{user_id}", response_model=MemberResponse, status_code=201)
async def add_member(group_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, Group, group_id, "Group not found")
    await get_entity_or_404(db, User, user_id, "User not found")

    stmt = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    db_member = GroupMember(group_id=group_id, user_id=user_id, role="member")
    db.add(db_member)
    try:
        await db.commit()
        await db.refresh(db_member)
        user = await db.get(User, user_id)
        return MemberResponse(id=user.id, phone_number=user.phone_number, username=user.username, role=db_member.role)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{group_id}/members/{user_id}")
async def remove_member(group_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    member = (await db.execute(stmt)).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in group")
    if member.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot remove admin")
    await db.delete(member)
    try:
        await db.commit()
        return {"detail": "Member removed"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{group_id}/members", response_model=List[MemberResponse])
async def get_group_members(group_id: int, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, Group, group_id, "Group not found")
    stmt = select(User, GroupMember.role).join(GroupMember).where(GroupMember.group_id == group_id)
    result = await db.execute(stmt)
    return [
        MemberResponse(id=u.id, phone_number=u.phone_number, username=u.username, role=role)
        for u, role in result.all()
    ]
