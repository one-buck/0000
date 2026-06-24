import enum
from sqlalchemy import Column, String, DateTime, Enum, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class NotificationType(str, enum.Enum):
    message = "message"
    system = "system"
    alert = "alert"

class NotificationStatus(str, enum.Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"

class GroupMembership(Base):
    __tablename__ = "group_memberships"
    group_id = Column(String, primary_key=True)
    user_id = Column(String, primary_key=True)

class UserDevice(Base):
    __tablename__ = "user_devices"
    user_id = Column(String, primary_key=True)
    device_id = Column(String, primary_key=True)
    connection_info = Column(JSON, nullable=True)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    group_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.pending)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))