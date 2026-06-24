import asyncio
from kafka_producer import KafkaProducerService

async def main():
    producer = KafkaProducerService("localhost:9092")
    await producer.start()
    
    print("Sending group message event...")
    await producer.send_group_event(
        group_id="group-1",
        sender_id="user-1",
        payload={
            "text": "Hello from user-1!",
            "timestamp": "2023-11-01T12:00:00Z"
        }
    )
    print("Message sent to Kafka topic 'group_events'.")
    
    await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())