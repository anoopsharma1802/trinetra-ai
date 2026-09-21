class KafkaEventPublisher:
    def __init__(self,bootstrap_servers): self.bootstrap_servers=bootstrap_servers
    async def publish(self,topic,payload): return {'topic':topic,'payload':payload,'status':'demo'}
