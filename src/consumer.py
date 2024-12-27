import pika
import json
from src.logger import logger


class RMQConsumer:
    def __init__(self, rabbitmq_url, exchange_name, queue_name, routing_key, max_queue_length=1000):
        """
        Initialize the RMQConsumer.
        :param rabbitmq_url: URL of the RabbitMQ server.
        :param exchange_name: Name of the exchange to bind to.
        :param queue_name: Name of the queue to declare.
        :param routing_key: Routing key for binding.
        :param max_queue_length: Maximum number of messages the queue can hold.
        """
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.max_queue_length = max_queue_length
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ and set up the queue."""
        try:
            logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url}")
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()

            # Declare the exchange
            self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='direct', durable=True)

            # Declare the queue with max length
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={"x-max-length": self.max_queue_length},
            )

            # Bind the queue to the exchange with the routing key
            self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.routing_key)
            logger.info(f"Queue '{self.queue_name}' bound to exchange '{self.exchange_name}' with routing key '{self.routing_key}'")
        except Exception as e:
            logger.error(f"Failed to connect and configure RabbitMQ: {e}", exc_info=True)
            raise

    def consume(self, message_callback):
        """
        Start consuming messages from the queue.
        :param message_callback: Function to process incoming messages.
        """
        try:
            logger.info(f"Starting to consume messages from queue: {self.queue_name}")
            for method, properties, body in self.channel.consume(queue=self.queue_name, auto_ack=False):
                try:
                    logger.debug(f"Received message: {body.decode()}")
                    message_callback(body.decode())  # Process the message
                    self.channel.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    self.channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  # Reject message
        except Exception as e:
            logger.error(f"Error during message consumption: {e}", exc_info=True)
            raise

    def close(self):
        """Close the RabbitMQ connection."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error while closing RabbitMQ connection: {e}", exc_info=True)
