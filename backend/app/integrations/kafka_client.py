import json


class KafkaEventPublisher:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers

    async def publish(self, topic, payload):
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
        try:
            await producer.start()
            await producer.send_and_wait(topic, json.dumps(payload).encode("utf-8"))
            return {"topic": topic, "status": "published"}
        except Exception as error:
            return {"topic": topic, "status": "unavailable", "error": str(error)}
        finally:
            await producer.stop()
