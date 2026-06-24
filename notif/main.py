import os
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from models import Base
from kafka_producer import KafkaProducerService
from kafka_consumer import KafkaConsumerService

# --- Config ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:password@localhost:5432/notification_db")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
VALID_API_KEYS = {"super-secret-api-key"} # In production, use DB/Auth service

# --- DB Setup ---
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# --- Kafka Setup ---
kafka_producer = KafkaProducerService(KAFKA_SERVERS)

# --- Connection Manager ---
class ConnectionManager:
    def __init__(self):
        # user_id -> device_id -> WebSocket
        self.active_connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)
        # user_id -> device_id -> list[payloads]
        self.pending_buffer: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    async def connect(self, user_id: str, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id][device_id] = websocket
        
        # Flush pending buffered messages on reconnect
        if user_id in self.pending_buffer and device_id in self.pending_buffer[user_id]:
            for payload in self.pending_buffer[user_id][device_id]:
                await websocket.send_json(payload)
            # Optionally update DB status to 'delivered' here
            del self.pending_buffer[user_id][device_id]

    def disconnect(self, user_id: str, device_id: str):
        if user_id in self.active_connections and device_id in self.active_connections[user_id]:
            del self.active_connections[user_id][device_id]

    def send_personal_message(self, user_id: str, device_id: str, payload: dict) -> bool:
        """Returns True if sent successfully, False if offline (buffers it)."""
        if user_id in self.active_connections and device_id in self.active_connections[user_id]:
            import asyncio
            ws = self.active_connections[user_id][device_id]
            # Fire and forget from sync context, or use asyncio.run_coroutine_threadsafe
            asyncio.create_task(ws.send_json(payload))
            return True
        return False

    def buffer_message(self, user_id: str, device_id: str, payload: dict):
        """Buffer message for when the client comes back online."""
        self.pending_buffer[user_id][device_id].append(payload)

ws_manager = ConnectionManager()
kafka_consumer = KafkaConsumerService(KAFKA_SERVERS, SessionLocal, kafka_producer, ws_manager)

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed dummy data for testing if tables are empty
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM group_memberships"))
        if result.scalar() == 0:
            await session.execute(text("INSERT INTO group_memberships (group_id, user_id) VALUES ('group-1', 'user-1')"))
            await session.execute(text("INSERT INTO group_memberships (group_id, user_id) VALUES ('group-1', 'user-2')"))
            await session.execute(text("INSERT INTO user_devices (user_id, device_id) VALUES ('user-1', 'device-1A')"))
            await session.execute(text("INSERT INTO user_devices (user_id, device_id) VALUES ('user-2', 'device-2A')"))
            await session.commit()

    await kafka_producer.start()
    
    # Start Kafka consumer in background
    import asyncio
    consumer_task = asyncio.create_task(kafka_consumer.start())
    
    yield
    
    # Shutdown
    consumer_task.cancel()
    await kafka_producer.stop()
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# --- WebSocket Endpoint ---
@app.websocket("/ws/{user_id}/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str, 
    device_id: str, 
    api_key: str = Query(...)
):
    if api_key not in VALID_API_KEYS:
        await websocket.close(code=4001, reason="Invalid API Key")
        return

    await ws_manager.connect(user_id, device_id, websocket)
    try:
        while True:
            # Keep connection open, handle client pings/pongs or incoming messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, device_id)

# --- HTTP Endpoint to trigger example (Optional, replaced by example_producer.py) ---
@app.get("/health")
async def health():
    return {"status": "ok"}