import dataclasses
import os


@dataclasses.dataclass
class RmqConfiguration:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    QUEUE_NAME = os.getenv("QUEUE_NAME", "market_data")
    EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "market_data_exchange")
    ROUTING_KEY = os.getenv("ROUTING_KEY", "market.data")
    QUEUE_LENGTH = os.getenv("QUEUE_LENGTH", 1000)
