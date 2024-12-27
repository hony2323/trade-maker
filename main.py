from src.consumer import MarketDataConsumer
from src.logger import logger


def process_market_data(message):
    """
    Process the incoming market data message.
    :param message: The parsed message from RabbitMQ.
    """
    # Example: Print the message or pass it to the trade evaluator
    logger.info(f"Processing market data: {message}")
    # Add your trade evaluation logic here


if __name__ == "__main__":
    RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"  # Update with your RabbitMQ connection URL
    QUEUE_NAME = "market_data"

    consumer = MarketDataConsumer(rabbitmq_url=RABBITMQ_URL, queue_name=QUEUE_NAME, process_callback=process_market_data)
    consumer.start_consuming()
