from src.configuration.trading_configuration import BinanceConfiguration
from src.io.consumer import RMQConsumer
from src.logger import logger
from src.configuration import RmqConfiguration
from src.trading.arbitrage_detector import ArbitrageDetector
from src.trading.exchanges.simulated_exchange import SimulatedExchange
from src.trading.fee_calculator import FeeCalculator
from src.trading.message_proccesor import MessageProcessor
from src.trading.position_manager import PositionManager
from src.trading.trade_evaluator import TradeEvaluator
from src.trading.trade_executer import TradeExecutor



if __name__ == '__main__':

    BYBIT_NAME = "Bybit"
    COINBASE_NAME = "Coinbase"
    KRAKEN_NAME = "Kraken"

    # Initialize SimulatedExchange instances
    coinbase = SimulatedExchange(COINBASE_NAME, initial_funds={"USDT": 1000})
    bybit = SimulatedExchange(BYBIT_NAME, initial_funds={"USDT": 1000})
    kraken = SimulatedExchange(KRAKEN_NAME, initial_funds={"USDT": 1000})

    # Create the ArbitrageDetector
    simulators = {COINBASE_NAME: coinbase, BYBIT_NAME: bybit, KRAKEN_NAME: kraken}
    arbitrage_detector = ArbitrageDetector(simulators, threshold=0.5)

    # Create the MessageProcessor
    processor = MessageProcessor(simulators, arbitrage_detector)

    # Simulate incoming data
    messages = [
        {"timestamp": 1735413478, "exchange": BYBIT_NAME, "instrument_id": "BTC-USD", "price": 95011.41},
        {"timestamp": 1735413480, "exchange": COINBASE_NAME, "instrument_id": "BTC-USD", "price": 96000.00},
        {"timestamp": 1735413482, "exchange": KRAKEN_NAME, "instrument_id": "BTC-USD", "price": 94000.00},
    ]

    # Process messages
    for msg in messages:
        processor.process_message(msg)


# if __name__ == "__main__":
#     # Trade Maker Components
#     trade_evaluator = TradeEvaluator(threshold=0.0)
#     trade_executor = TradeExecutor(
#         exchange_name="binance",
#         api_key=BinanceConfiguration.API_KEY,
#         api_secret=BinanceConfiguration.API_SECRET,
#         demo_mode=True,
#     )
#     position_manager = PositionManager()
#     fee_calculator = FeeCalculator(maker_fee=0.001, taker_fee=0.002)
#     message_processor = MessageProcessor(trade_evaluator, trade_executor, position_manager, fee_calculator)
#
#     consumer = RMQConsumer(rabbitmq_url=RmqConfiguration.RABBITMQ_URL,
#                            exchange_name=RmqConfiguration.EXCHANGE_NAME,
#                            queue_name=RmqConfiguration.QUEUE_NAME,
#                            routing_key=RmqConfiguration.ROUTING_KEY,
#                            max_queue_length=RmqConfiguration.QUEUE_LENGTH, )
#     def process_message(message):
#         """
#         Process an incoming message.
#         :param message: The message body as a string.
#         """
#         logger.debug(f"Processing message: {message}")
#         # Add your trade-making logic here
#         message_processor.process_message(message)
#
#     try:
#         consumer.connect()  # Connect to RabbitMQ
#         consumer.consume(process_message)  # Start consuming messages
#     except KeyboardInterrupt:
#         logger.info("Shutting down...")
#     finally:
#         consumer.close()  # Ensure the connection is closed properly
#         logger.info("Application stopped.")
