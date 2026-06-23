from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from sqlalchemy.exc import IntegrityError, SQLAlchemyError 
import datetime
from contextlib import asynccontextmanager
from typing import List, Optional

from database import engine, Base, get_db, User, Group, GroupMember, Message, MessageInbox
from schemas import MemberResponse, StatusUpdate, UserCreate, UserResponse, GroupCreate, GroupResponse, MessageSend, MessageResponse, UserUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="API", lifespan=lifespan)

async def get_entity_or_404(db: AsyncSession, model, id: int, detail: str = "Not found"):
    result = await db.execute(select(model).where(model.id == id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=detail)
    return entity

@app.post("/users/", response_model=UserResponse)
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

@app.get("/users/", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_entity_or_404(db, User, user_id, "User not found")

@app.put("/users/{user_id}", response_model=UserResponse)
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

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_entity_or_404(db, User, user_id, "User not found")
    await db.delete(user)
    try:
        await db.commit()
        return {"detail": "User deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/groups/", response_model=GroupResponse)
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

@app.get("/groups/", response_model=List[GroupResponse])
async def get_groups(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group).offset(skip).limit(limit))
    return result.scalars().all()

@app.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    return await get_entity_or_404(db, Group, group_id, "Group not found")

@app.delete("/groups/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await get_entity_or_404(db, Group, group_id, "Group not found")
    await db.delete(group)
    try:
        await db.commit()
        return {"detail": "Group deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/groups/{group_id}/members/{user_id}", response_model=MemberResponse)
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

@app.delete("/groups/{group_id}/members/{user_id}")
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

@app.get("/groups/{group_id}/members", response_model=List[MemberResponse])
async def get_group_members(group_id: int, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, Group, group_id, "Group not found")
    stmt = select(User, GroupMember.role).join(GroupMember).where(GroupMember.group_id == group_id)
    result = await db.execute(stmt)
    return [MemberResponse(id=u.id, phone_number=u.phone_number, username=u.username, role=role) for u, role in result.all()]

@app.post("/messages/", response_model=MessageResponse)
async def send_message(msg: MessageSend, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, msg.sender_id, "Sender not found")
    
    if msg.is_group_chat:
        await get_entity_or_404(db, Group, msg.receiver_id, "Group not found")
        is_member = await db.execute(
            select(exists().where(GroupMember.group_id == msg.receiver_id, GroupMember.user_id == msg.sender_id))
        )
        if not is_member.scalar():
            raise HTTPException(status_code=403, detail="Sender is not a member of the group")
    else:
        if msg.sender_id == msg.receiver_id:
            raise HTTPException(status_code=400, detail="Cannot send message to yourself")
        await get_entity_or_404(db, User, msg.receiver_id, "Receiver not found")

    db_msg = Message(sender_id=msg.sender_id, receiver_id=msg.receiver_id, content=msg.content, media_url=msg.media_url)
    db.add(db_msg)
    await db.flush()

    if msg.is_group_chat:
        stmt = select(GroupMember.user_id).where(GroupMember.group_id == msg.receiver_id)
        member_ids = [row[0] for row in (await db.execute(stmt)).fetchall()]
        for member_id in member_ids:
            if member_id != msg.sender_id:
                db.add(MessageInbox(user_id=member_id, message_id=db_msg.id))
    else:
        db.add(MessageInbox(user_id=msg.receiver_id, message_id=db_msg.id))

    try:
        await db.commit()
        await db.refresh(db_msg)
        return db_msg
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/inbox/{user_id}", response_model=List[MessageResponse])
async def get_user_inbox(user_id: int, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, user_id, "User not found")
    stmt = (
        select(Message)
        .join(MessageInbox, Message.id == MessageInbox.message_id)
        .where(MessageInbox.user_id == user_id, Message.is_deleted == False)
        .order_by(Message.timestamp.desc())
        .offset(skip).limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()

@app.get("/messages/history/", response_model=List[MessageResponse])
async def get_conversation_history(user_id: int, chat_id: int, is_group_chat: bool = False, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, user_id, "User not found")
    
    if is_group_chat:
        await get_entity_or_404(db, Group, chat_id, "Group not found")
        is_member = await db.execute(
            select(exists().where(GroupMember.group_id == chat_id, GroupMember.user_id == user_id))
        )
        if not is_member.scalar():
            raise HTTPException(status_code=403, detail="Not a member of this group")
            
        stmt = (
            select(Message)
            .where(Message.receiver_id == chat_id, Message.is_deleted == False)
            .order_by(Message.timestamp.asc())
            .offset(skip).limit(limit)
        )
    else:
        stmt = (
            select(Message)
            .where(
                Message.is_deleted == False,
                (
                    (Message.sender_id == user_id) & (Message.receiver_id == chat_id) |
                    (Message.sender_id == chat_id) & (Message.receiver_id == user_id)
                )
            )
            .order_by(Message.timestamp.asc())
            .offset(skip).limit(limit)
        )
    return (await db.execute(stmt)).scalars().all()

@app.put("/messages/{message_id}/status")
async def update_message_status(message_id: int, status_data: StatusUpdate, db: AsyncSession = Depends(get_db)):
    msg = await get_entity_or_404(db, Message, message_id, "Message not found")
    if status_data.status not in ["sent", "delivered", "read"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    msg.status = status_data.status
    try:
        await db.commit()
        return {"detail": "Status updated"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)