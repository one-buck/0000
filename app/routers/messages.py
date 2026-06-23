from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from database import get_db, User, Group, GroupMember, Message, MessageInbox
from schemas import MessageSend, MessageResponse, StatusUpdate
from utils import get_entity_or_404
import search

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/", response_model=MessageResponse, status_code=201)
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

    db_msg = Message(
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        media_url=msg.media_url,
    )
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
        await search.index_message(db_msg)
        return db_msg
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inbox/{user_id}", response_model=List[MessageResponse])
async def get_user_inbox(user_id: int, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    await get_entity_or_404(db, User, user_id, "User not found")
    stmt = (
        select(Message)
        .join(MessageInbox, Message.id == MessageInbox.message_id)
        .where(MessageInbox.user_id == user_id, Message.is_deleted == False)
        .order_by(Message.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/history/", response_model=List[MessageResponse])
async def get_conversation_history(
    user_id: int,
    chat_id: int,
    is_group_chat: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
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
            .offset(skip)
            .limit(limit)
        )
    else:
        stmt = (
            select(Message)
            .where(
                Message.is_deleted == False,
                (
                    (Message.sender_id == user_id) & (Message.receiver_id == chat_id)
                    | (Message.sender_id == chat_id) & (Message.receiver_id == user_id)
                ),
            )
            .order_by(Message.timestamp.asc())
            .offset(skip)
            .limit(limit)
        )
    return (await db.execute(stmt)).scalars().all()


@router.put("/{message_id}/status")
async def update_message_status(message_id: int, status_data: StatusUpdate, db: AsyncSession = Depends(get_db)):
    msg = await get_entity_or_404(db, Message, message_id, "Message not found")
    if status_data.status not in ("sent", "delivered", "read"):
        raise HTTPException(status_code=400, detail="Invalid status. Must be one of: sent, delivered, read")
    msg.status = status_data.status
    try:
        await db.commit()
        return {"detail": "Status updated"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{message_id}")
async def delete_message(message_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Soft-delete a message. Only the sender can delete it."""
    msg = await get_entity_or_404(db, Message, message_id, "Message not found")
    if msg.sender_id != user_id:
        raise HTTPException(status_code=403, detail="Only the sender can delete this message")
    msg.is_deleted = True
    try:
        await db.commit()
        await search.delete_message_doc(message_id)
        return {"detail": "Message deleted"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
