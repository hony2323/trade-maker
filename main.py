import json

from src.configuration import RmqConfiguration
from src.io.consumer import RMQConsumer
from src.logger import logger
from src.trading.arbitrage_detector import ArbitrageDetector
from src.trading.margin_simulated_exchange import MarginTradingSimulator
from src.trading.message_proccesor import MessageProcessor


def main():
    spread_threshold = 0.005  # 0.5% spread for arbitrage
    alignment_threshold = 0.001  # 0.1% spread for closing positions
    exchanges = ['Bybit', 'Coinbase', 'Kraken']
    initial_balance = 10000

    simulators = {exchange: MarginTradingSimulator(
        initial_balance,
        # {'maker': 0.001, 'taker': 0.002, 'borrow': 0.0001}, # maker 1%, taker 2%, borrow 0.01%
        {'maker': 0.0, 'taker': 0.0, 'borrow': 0.0}, # maker 1%, taker 2%, borrow 0.01%
        5,
        f'storage/{exchange}_simulator.json'
    ) for exchange in exchanges}

    detector = ArbitrageDetector(spread_threshold, alignment_threshold)
    message_processor = MessageProcessor(simulators, detector)

    consumer = RMQConsumer(rabbitmq_url=RmqConfiguration.RABBITMQ_URL,
                           exchange_name=RmqConfiguration.EXCHANGE_NAME,
                           queue_name=RmqConfiguration.QUEUE_NAME,
                           routing_key=RmqConfiguration.ROUTING_KEY,
                           max_queue_length=RmqConfiguration.QUEUE_LENGTH, )

    def process_message(message):
        """
        Process an incoming message.
        :param message: The message body as a string.
        """
        logger.debug(f"Processing message: {message}")
        message = json.loads(message)
        # Add your trade-making logic here
        message_processor.process_message(message)

    # Process each message
    try:
        consumer.connect()  # Connect to RabbitMQ
        consumer.consume(process_message)  # Start consuming messages
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        consumer.close()  # Ensure the connection is closed properly
        logger.info("Application stopped.")
        closed_positions = message_processor.close_all_positions()  # Close all open positions
        logger.info("Closed all open positions")

if __name__ == "__main__":
    main()
