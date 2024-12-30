import json

from src.configuration import RmqConfiguration
from src.io.consumer import RMQConsumer
from src.logger import logger
from src.trading.exchanges.simulated_exchange import SimulatedExchange
from src.trading.arbitrage_detector import ArbitrageDetector
from src.trading.message_proccesor import MessageProcessor

COINBASE_NAME = "Coinbase"
BYBIT_NAME = "Bybit"
KRAKEN_NAME = "Kraken"

def main():
    # Initialize exchanges with initial funds
    initial_funds = {"USD": 1000, "USDC": 1000, "EUR": 1000, "USDT": 1000}

    coinbase = SimulatedExchange(COINBASE_NAME, initial_funds=initial_funds, persist=True)
    bybit = SimulatedExchange(BYBIT_NAME, initial_funds=initial_funds, persist=True)
    kraken = SimulatedExchange(KRAKEN_NAME, initial_funds=initial_funds, persist=True)

    # Create ArbitrageDetector
    simulators = {COINBASE_NAME: coinbase, BYBIT_NAME: bybit, KRAKEN_NAME: kraken}
    arbitrage_detector = ArbitrageDetector(simulators, threshold=0.22)

    # Create MessageProcessor
    message_processor = MessageProcessor(simulators, arbitrage_detector, base_trade_amount=10)

    # # Perform a hard reset for all simulators (reset balances and persist)
    # for name, simulator in simulators.items():
    #     simulator.hard_reset(initial_funds=initial_funds)
    #     print(f"[{name.capitalize()}] Hard reset complete.")

    # Simulated price feed messages
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

    # Print final balances
    print("\nFinal Balances:")
    for name, simulator in simulators.items():
        print(f"{name.capitalize()}: {simulator.get_balance()}")

    # Print open positions
    print("\nOpen Positions:")
    for name, simulator in simulators.items():
        print(f"{name.capitalize()}: {simulator.positions}")


if __name__ == "__main__":
    main()
