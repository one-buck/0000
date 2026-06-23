"""
Quick reference for all API endpoints.
Run with: python3 tests/test_endpoints.py
Server must be running at http://127.0.0.1:8000
MinIO must be running at http://localhost:9000
Elasticsearch must be running at http://localhost:9200 (search section skipped if unavailable)
"""

import io
import time
import requests

BASE = "http://127.0.0.1:8000"


def section(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print('=' * 50)


def show(label, resp):
    print(f"\n-- {label} [{resp.status_code}] --")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


# ─────────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────────

section("USERS")

# Create users
resp = requests.post(f"{BASE}/users/", json={
    "phone_number": "+1000000001",
    "username": "alice"
})
show("Create user (alice)", resp)
alice_id = resp.json().get("id")

resp = requests.post(f"{BASE}/users/", json={
    "phone_number": "+1000000002",
    "username": "bob"
})
show("Create user (bob)", resp)
bob_id = resp.json().get("id")

resp = requests.post(f"{BASE}/users/", json={
    "phone_number": "+1000000003",
    "username": "carol"
})
show("Create user (carol)", resp)
carol_id = resp.json().get("id")

# List all users
resp = requests.get(f"{BASE}/users/")
show("List all users", resp)

# List users with pagination
resp = requests.get(f"{BASE}/users/", params={"skip": 0, "limit": 2})
show("List users (skip=0, limit=2)", resp)

# Search user by phone number
resp = requests.get(f"{BASE}/users/", params={"phone_number": "+1000000001"})
show("Search user by phone_number", resp)

# Get single user
resp = requests.get(f"{BASE}/users/{alice_id}")
show("Get user by id", resp)

# Update user
resp = requests.put(f"{BASE}/users/{alice_id}", json={"username": "alice_updated"})
show("Update user username", resp)

resp = requests.put(f"{BASE}/users/{alice_id}", json={"phone_number": "+1000000099"})
show("Update user phone_number", resp)
# Revert back so group/message tests don't care
requests.put(f"{BASE}/users/{alice_id}", json={"phone_number": "+1000000001"})

# Duplicate phone — expect 409
resp = requests.post(f"{BASE}/users/", json={"phone_number": "+1000000001", "username": "duplicate"})
show("Create user with duplicate phone (expect 409)", resp)

# Get user's groups (empty for now)
resp = requests.get(f"{BASE}/users/{alice_id}/groups")
show("Get user groups (empty)", resp)


# ─────────────────────────────────────────────────
# GROUPS
# ─────────────────────────────────────────────────

section("GROUPS")

# Create group
resp = requests.post(f"{BASE}/groups/", json={
    "name": "Team Alpha",
    "created_by": alice_id
})
show("Create group", resp)
group_id = resp.json().get("id")

# Create a second group
resp = requests.post(f"{BASE}/groups/", json={
    "name": "Team Beta",
    "created_by": bob_id
})
show("Create second group", resp)

# List groups
resp = requests.get(f"{BASE}/groups/")
show("List all groups", resp)

# Get single group
resp = requests.get(f"{BASE}/groups/{group_id}")
show("Get group by id", resp)

# Rename group
resp = requests.put(f"{BASE}/groups/{group_id}", json={"name": "Team Alpha Renamed"})
show("Rename group", resp)

# Add members
resp = requests.post(f"{BASE}/groups/{group_id}/members/{bob_id}")
show("Add bob to group", resp)

resp = requests.post(f"{BASE}/groups/{group_id}/members/{carol_id}")
show("Add carol to group", resp)

# Duplicate member — expect 409
resp = requests.post(f"{BASE}/groups/{group_id}/members/{bob_id}")
show("Add bob again (expect 409)", resp)

# List group members
resp = requests.get(f"{BASE}/groups/{group_id}/members")
show("List group members", resp)

# Get user's groups (now alice should appear)
resp = requests.get(f"{BASE}/users/{alice_id}/groups")
show("Get alice's groups", resp)

# Remove non-admin member
resp = requests.delete(f"{BASE}/groups/{group_id}/members/{carol_id}")
show("Remove carol from group", resp)

# Try removing admin — expect 400
resp = requests.delete(f"{BASE}/groups/{group_id}/members/{alice_id}")
show("Remove alice (admin) from group (expect 400)", resp)


# ─────────────────────────────────────────────────
# MESSAGES
# ─────────────────────────────────────────────────

section("MESSAGES")

# Send a direct message
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": alice_id,
    "receiver_id": bob_id,
    "content": "Hey Bob, how are you?"
})
show("Send DM alice → bob", resp)
dm_id = resp.json().get("id")

# Send another DM in the other direction
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": bob_id,
    "receiver_id": alice_id,
    "content": "Doing great Alice!"
})
show("Send DM bob → alice", resp)

# Send a message to yourself — expect 400
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": alice_id,
    "receiver_id": alice_id,
    "content": "talking to myself"
})
show("Send DM to self (expect 400)", resp)

# Send a group message
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": alice_id,
    "receiver_id": group_id,
    "content": "Hello team!",
    "is_group_chat": True
})
show("Send group message (alice → group)", resp)
group_msg_id = resp.json().get("id")

# Non-member tries to send to group — expect 403
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": carol_id,
    "receiver_id": group_id,
    "content": "sneaky message",
    "is_group_chat": True
})
show("Non-member sends group message (expect 403)", resp)

# Bob's inbox (should have the DM from alice + group message)
resp = requests.get(f"{BASE}/messages/inbox/{bob_id}")
show("Bob's inbox", resp)

# DM conversation history between alice and bob
resp = requests.get(f"{BASE}/messages/history/", params={
    "user_id": alice_id,
    "chat_id": bob_id,
    "is_group_chat": False
})
show("DM history alice ↔ bob", resp)

# Group conversation history
resp = requests.get(f"{BASE}/messages/history/", params={
    "user_id": alice_id,
    "chat_id": group_id,
    "is_group_chat": True
})
show("Group message history", resp)

# History with pagination
resp = requests.get(f"{BASE}/messages/history/", params={
    "user_id": alice_id,
    "chat_id": bob_id,
    "skip": 0,
    "limit": 1
})
show("DM history (limit=1)", resp)

# Update message status
resp = requests.put(f"{BASE}/messages/{dm_id}/status", json={"status": "delivered"})
show("Update message status → delivered", resp)

resp = requests.put(f"{BASE}/messages/{dm_id}/status", json={"status": "read"})
show("Update message status → read", resp)

# Invalid status — expect 400
resp = requests.put(f"{BASE}/messages/{dm_id}/status", json={"status": "flying"})
show("Invalid status (expect 400)", resp)

# Soft-delete a message
resp = requests.delete(f"{BASE}/messages/{dm_id}", params={"user_id": alice_id})
show("Soft-delete DM (sender)", resp)

# Someone else tries to delete — expect 403
resp = requests.delete(f"{BASE}/messages/{group_msg_id}", params={"user_id": bob_id})
show("Delete message as non-sender (expect 403)", resp)

# Inbox after deletion (deleted message should not appear)
resp = requests.get(f"{BASE}/messages/inbox/{bob_id}")
show("Bob's inbox after delete", resp)


# ─────────────────────────────────────────────────
# CONNECTIONS
# ─────────────────────────────────────────────────

section("CONNECTIONS")

# Register a connection (upsert)
resp = requests.put(f"{BASE}/connections/{alice_id}", json={
    "server_id": "server-1",
    "connection_id": "conn-abc-123",
    "device_type": "mobile"
})
show("Register alice's connection", resp)

resp = requests.put(f"{BASE}/connections/{bob_id}", json={
    "server_id": "server-1",
    "connection_id": "conn-xyz-456",
    "device_type": "desktop"
})
show("Register bob's connection", resp)

# Update (upsert again — same user, new connection_id)
resp = requests.put(f"{BASE}/connections/{alice_id}", json={
    "server_id": "server-2",
    "connection_id": "conn-abc-999",
    "device_type": "mobile"
})
show("Update alice's connection", resp)

# Get a user's connection
resp = requests.get(f"{BASE}/connections/{alice_id}")
show("Get alice's connection", resp)

# List all connections
resp = requests.get(f"{BASE}/connections/")
show("List all connections", resp)

# Filter connections by server
resp = requests.get(f"{BASE}/connections/", params={"server_id": "server-1"})
show("List connections on server-1", resp)

# Get connection for user with none — expect 404
resp = requests.get(f"{BASE}/connections/{carol_id}")
show("Get carol's connection (expect 404)", resp)

# Delete connection (e.g. on disconnect)
resp = requests.delete(f"{BASE}/connections/{bob_id}")
show("Delete bob's connection", resp)

resp = requests.delete(f"{BASE}/connections/{bob_id}")
show("Delete bob's connection again (expect 404)", resp)


# ─────────────────────────────────────────────────
# SEARCH  (skipped automatically if ES is down)
# ─────────────────────────────────────────────────

section("SEARCH")

es_available = requests.get(f"{BASE}/search/messages?q=test").status_code != 503

if not es_available:
    print("\n  [SKIPPED] Elasticsearch is not running — all search calls would return 503")
else:
    # ES needs a moment to make the indexed docs searchable
    time.sleep(1)

    # Search messages by content
    resp = requests.get(f"{BASE}/search/messages", params={"q": "how are you"})
    show("Search messages: 'how are you'", resp)

    # Fuzzy match (typo)
    resp = requests.get(f"{BASE}/search/messages", params={"q": "helo"})
    show("Search messages fuzzy: 'helo'", resp)

    # Filter by sender
    resp = requests.get(f"{BASE}/search/messages", params={"q": "hello", "sender_id": alice_id})
    show(f"Search messages from alice (id={alice_id})", resp)

    # Filter by receiver
    resp = requests.get(f"{BASE}/search/messages", params={"q": "hello", "receiver_id": bob_id})
    show(f"Search messages to bob (id={bob_id})", resp)

    # Filter by group receiver
    resp = requests.get(f"{BASE}/search/messages", params={"q": "team", "receiver_id": group_id})
    show(f"Search group messages (group_id={group_id})", resp)

    # Paginate
    resp = requests.get(f"{BASE}/search/messages", params={"q": "hello", "skip": 0, "limit": 1})
    show("Search messages (limit=1)", resp)

    # No results
    resp = requests.get(f"{BASE}/search/messages", params={"q": "xyzzy_no_match_zzzz"})
    show("Search messages: no results", resp)

    # Search groups by name
    resp = requests.get(f"{BASE}/search/groups", params={"q": "alpha"})
    show("Search groups: 'alpha'", resp)

    # Fuzzy group search
    resp = requests.get(f"{BASE}/search/groups", params={"q": "teem"})
    show("Search groups fuzzy: 'teem'", resp)

    # Paginate group search
    resp = requests.get(f"{BASE}/search/groups", params={"q": "team", "skip": 0, "limit": 1})
    show("Search groups (limit=1)", resp)

    # No results
    resp = requests.get(f"{BASE}/search/groups", params={"q": "xyzzy_no_match_zzzz"})
    show("Search groups: no results", resp)

    # Missing q param — expect 422
    resp = requests.get(f"{BASE}/search/messages")
    show("Missing q param (expect 422)", resp)


# ─────────────────────────────────────────────────
# MEDIA
# ─────────────────────────────────────────────────

section("MEDIA")

# Upload an image (fake PNG header bytes)
png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 200
resp = requests.post(
    f"{BASE}/media/upload",
    params={"uploader_id": alice_id},
    files={"file": ("photo.png", io.BytesIO(png_bytes), "image/png")},
)
show("Upload image", resp)
image_id = resp.json().get("id")
image_url = resp.json().get("url")

# Upload a video
resp = requests.post(
    f"{BASE}/media/upload",
    params={"uploader_id": alice_id},
    files={"file": ("clip.mp4", io.BytesIO(b'\x00ftyp' + b'\x00' * 100), "video/mp4")},
)
show("Upload video", resp)
video_id = resp.json().get("id")

# Upload an audio file
resp = requests.post(
    f"{BASE}/media/upload",
    params={"uploader_id": bob_id},
    files={"file": ("voice.ogg", io.BytesIO(b'OggS' + b'\x00' * 100), "audio/ogg")},
)
show("Upload audio", resp)
audio_id = resp.json().get("id")

# Upload a document
resp = requests.post(
    f"{BASE}/media/upload",
    params={"uploader_id": bob_id},
    files={"file": ("report.pdf", io.BytesIO(b'%PDF-1.4' + b'\x00' * 100), "application/pdf")},
)
show("Upload PDF", resp)
pdf_id = resp.json().get("id")

# Unsupported MIME type — expect 415
resp = requests.post(
    f"{BASE}/media/upload",
    params={"uploader_id": alice_id},
    files={"file": ("hack.exe", io.BytesIO(b'MZ' + b'\x00' * 20), "application/x-msdownload")},
)
show("Upload unsupported type (expect 415)", resp)

# Empty file — expect 400
resp = requests.post(
    f"{BASE}/media/upload",
    params={"uploader_id": alice_id},
    files={"file": ("empty.png", io.BytesIO(b''), "image/png")},
)
show("Upload empty file (expect 400)", resp)

# List all media
resp = requests.get(f"{BASE}/media/")
show("List all media", resp)

# Filter by uploader
resp = requests.get(f"{BASE}/media/", params={"uploader_id": alice_id})
show("List alice's media", resp)

# Filter by kind
resp = requests.get(f"{BASE}/media/", params={"kind": "audio"})
show("Filter by kind=audio", resp)

# Filter by uploader + kind
resp = requests.get(f"{BASE}/media/", params={"uploader_id": bob_id, "kind": "file"})
show("Bob's files only", resp)

# Paginate
resp = requests.get(f"{BASE}/media/", params={"skip": 0, "limit": 2})
show("List media (limit=2)", resp)

# Get single media record
resp = requests.get(f"{BASE}/media/{image_id}")
show("Get media by id", resp)

# Get non-existent — expect 404
resp = requests.get(f"{BASE}/media/99999")
show("Get missing media (expect 404)", resp)

# Send a message with a media_url (image)
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": alice_id,
    "receiver_id": bob_id,
    "content": None,
    "media_url": image_url,
})
show("Send DM with image attachment", resp)

# Send a group message with audio
resp = requests.post(f"{BASE}/messages/", json={
    "sender_id": alice_id,
    "receiver_id": group_id,
    "content": "Listen to this",
    "media_url": resp.json().get("media_url"),
    "is_group_chat": True,
})
show("Send group message with media", resp)

# Delete media as wrong user — expect 403
resp = requests.delete(f"{BASE}/media/{image_id}", params={"requester_id": bob_id})
show("Delete image as bob (expect 403)", resp)

# Delete media as uploader
resp = requests.delete(f"{BASE}/media/{image_id}", params={"requester_id": alice_id})
show("Delete image as alice (uploader)", resp)

resp = requests.delete(f"{BASE}/media/{video_id}", params={"requester_id": alice_id})
show("Delete video", resp)

resp = requests.delete(f"{BASE}/media/{audio_id}", params={"requester_id": bob_id})
show("Delete audio", resp)

resp = requests.delete(f"{BASE}/media/{pdf_id}", params={"requester_id": bob_id})
show("Delete PDF", resp)

# Confirm deleted — expect 404
resp = requests.get(f"{BASE}/media/{image_id}")
show("Get deleted media (expect 404)", resp)


# ─────────────────────────────────────────────────
# TEARDOWN  (optional — comment out to keep data)
# ─────────────────────────────────────────────────

section("TEARDOWN")

for gid in [group_id]:
    resp = requests.delete(f"{BASE}/groups/{gid}")
    show(f"Delete group {gid}", resp)

for uid in [alice_id, bob_id, carol_id]:
    resp = requests.delete(f"{BASE}/users/{uid}")
    show(f"Delete user {uid}", resp)

print("\nDone.\n")
