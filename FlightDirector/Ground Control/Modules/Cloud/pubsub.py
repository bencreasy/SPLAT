from google.cloud import pubsub_v1
import json

class PubSubHandler:
    """
    Handles pub/sub communication with GCP.
    Manages message topics and subscriptions.
    """
    def __init__(self, config: dict):
        self.config = config
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.topics = {}
        
    async def initialize(self):
        """Initialize pub/sub connections"""
        # Set up standard topics
        self.topics = {
            'telemetry': self._get_topic_path('telemetry'),
            'status': self._get_topic_path('status'),
            'alerts': self._get_topic_path('alerts'),
            'commands': self._get_topic_path('commands')
        }
        
        # Start command subscription
        await self._start_command_subscription()
        
    async def publish(self, topic: str, data: Dict[str, Any], 
                     retry: int = 3) -> bool:
        """Publish message to topic"""
        if topic not in self.topics:
            raise ValueError(f"Unknown topic: {topic}")
            
        try:
            # Prepare message
            message = json.dumps(data).encode('utf-8')
            
            # Publish with retry
            for attempt in range(retry):
                try:
                    future = self.publisher.publish(
                        self.topics[topic],
                        message
                    )
                    return await future
                except Exception as e:
                    if attempt == retry - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
                    
        except Exception as e:
            raise PublishError(f"Failed to publish to {topic}: {str(e)}")
