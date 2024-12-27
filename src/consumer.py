import pika
import json
from src.logger import logger


class MarketDataConsumer:
    def __init__(self, rabbitmq_url, queue_name, process_callback):
        """
        Initialize the RabbitMQ consumer.
        :param rabbitmq_url: URL of the RabbitMQ server.
        :param queue_name: Name of the queue to consume from.
        :param process_callback: Function to process incoming messages.
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.process_callback = process_callback

    def _on_message(self, channel, method, properties, body):
        """Callback function to handle incoming messages."""
        try:
            message = json.loads(body)
            logger.info(f"Received message: {message}")
            self.process_callback(message)
            channel.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  # Reject message

    def start_consuming(self):
        """Start consuming messages from the queue."""
        connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
        channel = connection.channel()

        # Declare the queue (in case it hasn't been created)
        channel.queue_declare(queue=self.queue_name, durable=True)

        logger.info(f"Starting to consume from queue: {self.queue_name}")
        channel.basic_consume(queue=self.queue_name, on_message_callback=self._on_message)

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            connection.close()
