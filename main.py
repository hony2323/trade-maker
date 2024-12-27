from src.consumer import RMQConsumer
from src.logger import logger
from src.configuration import RmqConfiguration


def process_message(message):
    """
    Process an incoming message.
    :param message: The message body as a string.
    """
    logger.debug(f"Processing message: {message}")
    # Add your trade-making logic here


if __name__ == "__main__":

    consumer = RMQConsumer(rabbitmq_url=RmqConfiguration.RABBITMQ_URL,
                                   exchange_name=RmqConfiguration.EXCHANGE_NAME,
                                   queue_name=RmqConfiguration.QUEUE_NAME,
                                   routing_key=RmqConfiguration.ROUTING_KEY,
                                   max_queue_length=RmqConfiguration.QUEUE_LENGTH,)
    try:
        consumer.connect()  # Connect to RabbitMQ
        consumer.consume(process_message)  # Start consuming messages
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        consumer.close()  # Ensure the connection is closed properly
        logger.info("Application stopped.")
