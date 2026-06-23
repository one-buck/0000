"""
Elasticsearch integration.

Indices
-------
  chat-messages  — indexes Message rows (content, sender_id, receiver_id, timestamp)
  chat-groups    — indexes Group rows (name, created_by, created_at)

The client is initialised lazily; if ES is unreachable the helpers raise
HTTPException(503) so the rest of the API keeps working.
"""

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from fastapi import HTTPException

from config import settings

_client: AsyncElasticsearch | None = None

MESSAGE_INDEX = "chat-messages"
GROUP_INDEX = "chat-groups"

MESSAGE_MAPPING = {
    "mappings": {
        "properties": {
            "id":          {"type": "integer"},
            "sender_id":   {"type": "integer"},
            "receiver_id": {"type": "integer"},
            "content":     {"type": "text", "analyzer": "standard"},
            "status":      {"type": "keyword"},
            "timestamp":   {"type": "date"},
            "is_deleted":  {"type": "boolean"},
        }
    }
}

GROUP_MAPPING = {
    "mappings": {
        "properties": {
            "id":         {"type": "integer"},
            "name":       {"type": "text", "analyzer": "standard"},
            "created_by": {"type": "integer"},
            "created_at": {"type": "date"},
        }
    }
}


def get_client() -> AsyncElasticsearch:
    global _client
    if _client is None:
        _client = AsyncElasticsearch(
            f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}",
        )
    return _client


async def ensure_indices() -> None:
    """Create indices if they don't exist. Called once at startup."""
    es = get_client()
    for index, mapping in [(MESSAGE_INDEX, MESSAGE_MAPPING), (GROUP_INDEX, GROUP_MAPPING)]:
        if not await es.indices.exists(index=index):
            await es.indices.create(index=index, body=mapping)


async def _es_or_503(coro):
    """For search queries — fail loudly if ES is down."""
    try:
        return await coro
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="Search service unavailable")


async def _es_silent(coro):
    """For background indexing — swallow errors so the main operation always succeeds."""
    try:
        await coro
    except Exception:
        pass


# ── Messages ──────────────────────────────────────────────────────────────────

async def index_message(msg) -> None:
    await _es_silent(get_client().index(
        index=MESSAGE_INDEX,
        id=str(msg.id),
        document={
            "id":          msg.id,
            "sender_id":   msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content":     msg.content or "",
            "status":      msg.status,
            "timestamp":   msg.timestamp.isoformat(),
            "is_deleted":  msg.is_deleted,
        },
    ))


async def delete_message_doc(message_id: int) -> None:
    try:
        await get_client().delete(index=MESSAGE_INDEX, id=str(message_id))
    except (NotFoundError, ESConnectionError):
        pass


async def search_messages(
    query: str,
    sender_id: int | None = None,
    receiver_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    must = [
        {"match": {"content": {"query": query, "fuzziness": "AUTO"}}},
        {"term": {"is_deleted": False}},
    ]
    if sender_id is not None:
        must.append({"term": {"sender_id": sender_id}})
    if receiver_id is not None:
        must.append({"term": {"receiver_id": receiver_id}})

    body = {
        "from": skip,
        "size": limit,
        "query": {"bool": {"must": must}},
        "sort": [{"timestamp": "desc"}],
    }
    resp = await _es_or_503(get_client().search(index=MESSAGE_INDEX, body=body))
    return [hit["_source"] for hit in resp["hits"]["hits"]]


# ── Groups ────────────────────────────────────────────────────────────────────

async def index_group(group) -> None:
    await _es_silent(get_client().index(
        index=GROUP_INDEX,
        id=str(group.id),
        document={
            "id":         group.id,
            "name":       group.name,
            "created_by": group.created_by,
            "created_at": group.created_at.isoformat(),
        },
    ))


async def delete_group_doc(group_id: int) -> None:
    try:
        await get_client().delete(index=GROUP_INDEX, id=str(group_id))
    except (NotFoundError, ESConnectionError):
        pass


async def search_groups(query: str, skip: int = 0, limit: int = 50) -> list[dict]:
    body = {
        "from": skip,
        "size": limit,
        "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
        "sort": [{"created_at": "desc"}],
    }
    resp = await _es_or_503(get_client().search(index=GROUP_INDEX, body=body))
    return [hit["_source"] for hit in resp["hits"]["hits"]]
