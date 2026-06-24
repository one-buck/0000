import json
import logging
import uuid
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import GroupMembership, UserDevice, Notification, NotificationType, NotificationStatus
from kafka_producer import KafkaProducerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self, bootstrap_servers: str, session_factory: async_sessionmaker, producer: KafkaProducerService, connection_manager):
        self.bootstrap_servers = bootstrap_servers
        self.session_factory = session_factory
        self.producer = producer
        self.connection_manager = connection_manager
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            "group_events",
            bootstrap_servers=self.bootstrap_servers,
            group_id="notification-fanout-group",
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset="earliest"
        )
        await self.consumer.start()
        logger.info("Kafka consumer started. Waiting for messages...")
        
        try:
            async for msg in self.consumer:
                await self._process_message(msg)
        except Exception as e:
            logger.error(f"Consumer crashed: {e}")
        finally:
            await self.consumer.stop()

    async def _process_message(self, msg):
        try:
            data = msg.value
            group_id = data["group_id"]
            sender_id = data["sender_id"]
            payload = data["payload"]
            notif_type = NotificationType.message 

            async with self.session_factory() as session:
                # 1. Resolve group members
                result = await session.execute(
                    select(GroupMembership).where(GroupMembership.group_id == group_id)
                )
                members = result.scalars().all()
                user_ids = [m.user_id for m in members if m.user_id != sender_id] # Exclude sender

                if not user_ids:
                    logger.info(f"No other members in group {group_id}. Skipping.")
                    return

                # 2. Resolve devices for all users
                result = await session.execute(
                    select(UserDevice).where(UserDevice.user_id.in_(user_ids))
                )
                devices = result.scalars().all()

                # 3 & 4. Produce per-device events, Store in Postgres, Push to WS
                for device in devices:
                    notif_id = str(uuid.uuid4())
                    
                    notification = Notification(
                        id=notif_id,
                        group_id=group_id,
                        user_id=device.user_id,
                        device_id=device.device_id,
                        type=notif_type,
                        payload=payload,
                        status=NotificationStatus.pending
                    )
                    session.add(notification)
                    
                    # Produce per-device event
                    await self.producer.send_device_event(
                        user_id=device.user_id,
                        device_id=device.device_id,
                        notification_id=notif_id,
                        payload=payload,
                        notif_type=notif_type
                    )

                    # Push to WebSocket directly
                    is_delivered = self.connection_manager.send_personal_message(
                        device.user_id, device.device_id, payload
                    )

                    if is_delivered:
                        notification.status = NotificationStatus.delivered
                    else:
                        # Buffered locally by ConnectionManager for when they reconnect
                        self.connection_manager.buffer_message(device.user_id, device.device_id, payload)

                await session.commit()
                logger.info(f"Processed fan-out for group {group_id} to {len(devices)} devices.")

        except Exception as e:
            logger.error(f"Error processing message: {e}. Sending to DLQ.")
            await self.producer.send_to_dlq(msg.topic, msg.value, str(e))
            