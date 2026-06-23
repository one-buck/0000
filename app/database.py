from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, func
import datetime
from typing import List, Optional
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    groups: Mapped[list["GroupMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sent_messages: Mapped[list["Message"]] = relationship(back_populates="sender", foreign_keys="[Message.sender_id]", cascade="all, delete-orphan")
    inbox: Mapped[list["MessageInbox"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    connections: Mapped[list["UserConnection"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    members: Mapped[list["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")

class GroupMember(Base):
    __tablename__ = "group_members"
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    role: Mapped[str] = mapped_column(String, default="member")
    joined_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="groups")
    group: Mapped["Group"] = relationship(back_populates="members")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id: Mapped[int] = mapped_column(Integer)
    content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="sent")
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    sender: Mapped["User"] = relationship(back_populates="sent_messages", foreign_keys=[sender_id])
    inbox_entries: Mapped[list["MessageInbox"]] = relationship(back_populates="message", cascade="all, delete-orphan")

class MessageInbox(Base):
    __tablename__ = "message_inbox"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="inbox")
    message: Mapped["Message"] = relationship(back_populates="inbox_entries")

class UserConnection(Base):
    __tablename__ = "user_connection_registry"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    server_id: Mapped[str] = mapped_column(String)
    connection_id: Mapped[str] = mapped_column(String)
    last_active: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    device_type: Mapped[str] = mapped_column(String)

    user: Mapped["User"] = relationship(back_populates="connections")

class Media(Base):
    __tablename__ = "media"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uploader_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    object_name: Mapped[str] = mapped_column(String, unique=True)
    url: Mapped[str] = mapped_column(String)
    filename: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)  # image | video | audio | file
    size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uploader: Mapped["User"] = relationship()