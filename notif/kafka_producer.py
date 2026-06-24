import json
import uuid
from aiokafka import AIOKafkaProducer
import asyncio

class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_group_event(self, group_id: str, sender_id: str, payload: dict):
        """Publishes group message event. Partitioned by group_id."""
        event = {
            "group_id": group_id,
            "sender_id": sender_id,
            "payload": payload
        }
        # Key ensures ordering per group_id
        await self.producer.send_and_wait("group_events", key=group_id, value=event)

    async def send_device_event(self, user_id: str, device_id: str, notification_id: str, payload: dict, notif_type: str):
        """Publishes per-device notification event."""
        event = {
            "notification_id": notification_id,
            "user_id": user_id,
            "device_id": device_id,
            "type": notif_type,
            "payload": payload
        }
        # Key ensures ordering per user
        await self.producer.send_and_wait("device_notifications", key=user_id, value=event)

    async def send_to_dlq(self, topic: str, raw_value: bytes, error: str):
        """Sends failed messages to Dead Letter Queue."""
        await self.producer.send_and_wait("dlq_topic", value={
            "origin_topic": topic,
            "error": str(error),
            "raw_data": raw_value.decode('utf-8', errors='replace')
        })