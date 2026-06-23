from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    phone_number: str
    username: str

class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    phone_number: str
    username: str
    created_at: datetime
    last_seen: datetime
    class Config:
        from_attributes = True


class GroupCreate(BaseModel):
    name: str
    created_by: int

class GroupUpdate(BaseModel):
    name: str

class GroupResponse(BaseModel):
    id: int
    name: str
    created_by: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    id: int
    phone_number: str
    username: str
    role: str
    class Config:
        from_attributes = True


class MessageSend(BaseModel):
    sender_id: int
    receiver_id: int
    content: Optional[str] = None
    media_url: Optional[str] = None
    is_group_chat: bool = False

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: Optional[str]
    media_url: Optional[str]
    status: str
    timestamp: datetime
    is_deleted: bool
    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str


class MediaResponse(BaseModel):
    id: int
    uploader_id: int
    url: str
    filename: str
    kind: str
    size: int
    uploaded_at: datetime
    class Config:
        from_attributes = True


class ConnectionUpsert(BaseModel):
    server_id: str
    connection_id: str
    device_type: str

class ConnectionResponse(BaseModel):
    user_id: int
    server_id: str
    connection_id: str
    device_type: str
    last_active: datetime
    class Config:
        from_attributes = True
