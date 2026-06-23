# Chat API — Developer Reference

Base URL: `http://127.0.0.1:8000`  
Interactive docs: `http://127.0.0.1:8000/docs`

---

## Setup

```bash
# Start the database + object storage
docker compose --env-file .env up -d postgres minio

# Run the server
source venv/bin/activate
python3 app/main.py
```

---

## Users

### `POST /users/`
Create a new user.

**Body**
```json
{ "phone_number": "+1234567890", "username": "alice" }
```

**Responses**
| Status | Meaning |
|--------|---------|
| `201` | User created |
| `409` | Phone number already registered |

**Example response**
```json
{
  "id": 1,
  "phone_number": "+1234567890",
  "username": "alice",
  "created_at": "2026-06-23T12:00:00Z",
  "last_seen": "2026-06-23T12:00:00Z"
}
```

---

### `GET /users/`
List all users. Supports pagination and phone number search.

**Query params**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | `0` | Number of records to skip |
| `limit` | int | `50` | Max records to return |
| `phone_number` | string | — | Exact match filter |

**Examples**
```
GET /users/
GET /users/?skip=0&limit=10
GET /users/?phone_number=+1234567890
```

---

### `GET /users/{user_id}`
Get a single user by ID.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | User found |
| `404` | User not found |

---

### `PUT /users/{user_id}`
Update a user's username and/or phone number. Send only the fields you want to change.

**Body**
```json
{ "username": "alice_new" }
```

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Updated |
| `404` | User not found |
| `409` | Phone number already taken |

---

### `DELETE /users/{user_id}`
Permanently delete a user. Cascades to their messages, group memberships, and inbox entries.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "User deleted successfully"}` |
| `404` | User not found |

---

### `GET /users/{user_id}/groups`
List all groups the user is a member of.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Array of group objects (empty array if none) |
| `404` | User not found |

---

## Groups

### `POST /groups/`
Create a new group. The creator is automatically added as `admin`.

**Body**
```json
{ "name": "Team Alpha", "created_by": 1 }
```

**Responses**
| Status | Meaning |
|--------|---------|
| `201` | Group created |
| `404` | Creator user not found |

**Example response**
```json
{
  "id": 1,
  "name": "Team Alpha",
  "created_by": 1,
  "created_at": "2026-06-23T12:00:00Z"
}
```

---

### `GET /groups/`
List all groups.

**Query params**
| Param | Type | Default |
|-------|------|---------|
| `skip` | int | `0` |
| `limit` | int | `50` |

---

### `GET /groups/{group_id}`
Get a single group by ID.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Group found |
| `404` | Group not found |

---

### `PUT /groups/{group_id}`
Rename a group.

**Body**
```json
{ "name": "Team Alpha Renamed" }
```

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Updated |
| `404` | Group not found |

---

### `DELETE /groups/{group_id}`
Delete a group and all its members and messages.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "Group deleted successfully"}` |
| `404` | Group not found |

---

### `POST /groups/{group_id}/members/{user_id}`
Add a user to a group as `member`.

**Responses**
| Status | Meaning |
|--------|---------|
| `201` | Member added — returns `MemberResponse` |
| `404` | Group or user not found |
| `409` | User is already a member |

**Example response**
```json
{
  "id": 2,
  "phone_number": "+9876543210",
  "username": "bob",
  "role": "member"
}
```

---

### `DELETE /groups/{group_id}/members/{user_id}`
Remove a member from a group. Admins cannot be removed.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "Member removed"}` |
| `400` | Cannot remove admin |
| `404` | Member not found in group |

---

### `GET /groups/{group_id}/members`
List all members of a group with their roles.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Array of member objects |
| `404` | Group not found |

**Example response**
```json
[
  { "id": 1, "phone_number": "+1234567890", "username": "alice", "role": "admin" },
  { "id": 2, "phone_number": "+9876543210", "username": "bob",   "role": "member" }
]
```

---

## Messages

### `POST /messages/`
Send a direct message or a group message.

**Body**
```json
{
  "sender_id": 1,
  "receiver_id": 2,
  "content": "Hey!",
  "media_url": null,
  "is_group_chat": false
}
```

| Field | Type | Notes |
|-------|------|-------|
| `sender_id` | int | Must exist |
| `receiver_id` | int | User ID for DMs, Group ID for group chat |
| `content` | string \| null | At least one of `content` or `media_url` is expected |
| `media_url` | string \| null | URL to an uploaded file |
| `is_group_chat` | bool | `false` = DM, `true` = group message |

**Responses**
| Status | Meaning |
|--------|---------|
| `201` | Message sent |
| `400` | Cannot send message to yourself |
| `403` | Sender is not a group member |
| `404` | Sender, receiver, or group not found |

**Example response**
```json
{
  "id": 5,
  "sender_id": 1,
  "receiver_id": 2,
  "content": "Hey!",
  "media_url": null,
  "status": "sent",
  "timestamp": "2026-06-23T12:00:00Z",
  "is_deleted": false
}
```

---

### `GET /messages/inbox/{user_id}`
Get all unread/received messages for a user, newest first. Excludes soft-deleted messages.

**Query params**
| Param | Type | Default |
|-------|------|---------|
| `skip` | int | `0` |
| `limit` | int | `50` |

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Array of message objects |
| `404` | User not found |

---

### `GET /messages/history/`
Get the full conversation history between two users, or all messages in a group. Ordered oldest → newest.

**Query params**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | int | yes | The requesting user |
| `chat_id` | int | yes | The other user ID (DM) or group ID |
| `is_group_chat` | bool | no (`false`) | Set `true` for group history |
| `skip` | int | no (`0`) | Pagination offset |
| `limit` | int | no (`50`) | Page size |

**Examples**
```
GET /messages/history/?user_id=1&chat_id=2
GET /messages/history/?user_id=1&chat_id=3&is_group_chat=true
GET /messages/history/?user_id=1&chat_id=2&skip=0&limit=20
```

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Array of message objects |
| `403` | User is not a group member |
| `404` | User or group not found |

---

### `PUT /messages/{message_id}/status`
Update a message's delivery status.

**Body**
```json
{ "status": "delivered" }
```

Valid values: `"sent"` → `"delivered"` → `"read"`

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "Status updated"}` |
| `400` | Invalid status value |
| `404` | Message not found |

---

### `DELETE /messages/{message_id}`
Soft-delete a message (sets `is_deleted = true`). Only the sender can delete. The message is hidden from inboxes and history but not removed from the database.

**Query params**
| Param | Type | Required |
|-------|------|----------|
| `user_id` | int | yes |

**Example**
```
DELETE /messages/5?user_id=1
```

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "Message deleted"}` |
| `403` | Requester is not the sender |
| `404` | Message not found |

---

## Connections

Used to track which WebSocket connection belongs to which user (e.g. for routing real-time messages across servers).

### `PUT /connections/{user_id}`
Register or update a user's active connection. Safe to call on every reconnect.

**Body**
```json
{
  "server_id": "server-1",
  "connection_id": "conn-abc-123",
  "device_type": "mobile"
}
```

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Connection registered or updated |
| `404` | User not found |

**Example response**
```json
{
  "user_id": 1,
  "server_id": "server-1",
  "connection_id": "conn-abc-123",
  "device_type": "mobile",
  "last_active": "2026-06-23T12:00:00Z"
}
```

---

### `GET /connections/{user_id}`
Get the active connection record for a user.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Connection found |
| `404` | User not found or no active connection |

---

### `DELETE /connections/{user_id}`
Remove a user's connection record (call on WebSocket disconnect).

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "Connection removed"}` |
| `404` | No active connection found |

---

### `GET /connections/`
List all active connections, optionally filtered by server.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| `server_id` | string | Filter to one server instance |

**Examples**
```
GET /connections/
GET /connections/?server_id=server-1
```

---

## Media

Media must be uploaded before being attached to a message. The upload returns a URL you pass as `media_url` in `POST /messages/`.

**Supported types and size limits**

| Kind | MIME types | Max size |
|------|-----------|---------|
| `image` | `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/heic` | 10 MB |
| `video` | `video/mp4`, `video/quicktime`, `video/webm`, `video/x-matroska` | 200 MB |
| `audio` | `audio/mpeg`, `audio/ogg`, `audio/wav`, `audio/aac`, `audio/webm` | 50 MB |
| `file` | `application/pdf`, `application/zip`, `text/plain`, Word docs, `application/octet-stream` | 50 MB |

Files are stored in MinIO under `chat-media/{kind}/{uuid}.{ext}` and served via a public URL.

---

### `POST /media/upload`
Upload a file. Sent as `multipart/form-data`.

**Query params**
| Param | Type | Required |
|-------|------|----------|
| `uploader_id` | int | yes |

**Form field**: `file` — the binary file

**Example (curl)**
```bash
curl -X POST "http://127.0.0.1:8000/media/upload?uploader_id=1" \
  -F "file=@photo.jpg"
```

**Responses**
| Status | Meaning |
|--------|---------|
| `201` | Uploaded — returns `MediaResponse` |
| `400` | Empty file |
| `404` | Uploader not found |
| `413` | File exceeds size limit |
| `415` | Unsupported MIME type |

**Example response**
```json
{
  "id": 1,
  "uploader_id": 1,
  "url": "http://localhost:9000/chat-media/image/uuid.jpg",
  "filename": "photo.jpg",
  "kind": "image",
  "size": 204800,
  "uploaded_at": "2026-06-23T12:00:00Z"
}
```

---

### `GET /media/`
List uploaded media records.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| `uploader_id` | int | Filter by uploader |
| `kind` | string | Filter by type: `image`, `video`, `audio`, `file` |
| `skip` | int | Pagination offset (default `0`) |
| `limit` | int | Page size (default `50`) |

**Examples**
```
GET /media/
GET /media/?uploader_id=1
GET /media/?kind=video
GET /media/?uploader_id=1&kind=audio
```

---

### `GET /media/{media_id}`
Get a single media record by ID.

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | Found |
| `404` | Not found |

---

### `DELETE /media/{media_id}`
Delete a media record and remove the file from MinIO. Only the uploader can delete.

**Query params**
| Param | Type | Required |
|-------|------|----------|
| `requester_id` | int | yes |

**Example**
```
DELETE /media/3?requester_id=1
```

**Responses**
| Status | Meaning |
|--------|---------|
| `200` | `{"detail": "Media deleted"}` |
| `403` | Requester is not the uploader |
| `404` | Media not found |

---

## Data Models

### User
| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Auto-increment PK |
| `phone_number` | string | Unique |
| `username` | string | Display name |
| `created_at` | datetime | UTC |
| `last_seen` | datetime | Updated on PUT |

### Group
| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Auto-increment PK |
| `name` | string | |
| `created_by` | int \| null | FK → users, SET NULL on delete |
| `created_at` | datetime | UTC |

### Message
| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Auto-increment PK |
| `sender_id` | int | FK → users |
| `receiver_id` | int | User ID (DM) or Group ID (group chat) |
| `content` | string \| null | |
| `media_url` | string \| null | |
| `status` | string | `sent` / `delivered` / `read` |
| `timestamp` | datetime | UTC |
| `is_deleted` | bool | Soft-delete flag |

### Connection
| Field | Type | Notes |
|-------|------|-------|
| `user_id` | int | PK, FK → users |
| `server_id` | string | Which server holds this socket |
| `connection_id` | string | Unique ID for the socket |
| `device_type` | string | e.g. `mobile`, `desktop`, `web` |
| `last_active` | datetime | Set on creation |

### Media
| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Auto-increment PK |
| `uploader_id` | int | FK → users, CASCADE on delete |
| `object_name` | string | MinIO object key, e.g. `image/uuid.jpg` |
| `url` | string | Direct public URL to the file |
| `filename` | string | Original filename from the upload |
| `kind` | string | `image` / `video` / `audio` / `file` |
| `size` | int | File size in bytes |
| `uploaded_at` | datetime | UTC |

---

## Error Format

All errors return JSON:
```json
{ "detail": "Human-readable error message" }
```
