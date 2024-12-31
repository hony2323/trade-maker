import time

from src.trading.arbitrage_detector import ArbitrageDetector
from src.trading.margin_simulated_exchange import MarginTradingSimulator
from src.trading.message_proccesor import MessageProcessor


def main():
    # Configuration
    spread_threshold = 0.005  # Minimum spread for arbitrage opportunity
    alignment_threshold = 0.001  # Spread threshold to close positions
    exchanges = ['Bybit', 'Binance']
    symbols = ['ADA-USD', 'BTC-USD']
    initial_balance = 10000  # Starting balance for each simulator

    # Initialize Simulators
    simulators = {exchange: MarginTradingSimulator(
        initial_balance,
        {'maker': 0.001, 'taker': 0.002, 'borrow': 0.0001},
        5,
        f'{exchange}_simulator.json'
    ) for exchange in exchanges}

    # Initialize Detector and Processor
    detector = ArbitrageDetector(spread_threshold, alignment_threshold)
    processor = MessageProcessor(simulators, detector)

    # Simulate Messages
    messages = [
        # Initial arbitrage opportunity
        {'24h_volume': 18594708.87, 'best_ask': 0.8482, 'best_bid': 0.8482, 'exchange': 'Bybit', 'instrument_id': 'ADA-USD', 'price': 0.8482, 'timestamp': time.time()},
        {'24h_volume': 19000000, 'best_ask': 0.845, 'best_bid': 0.845, 'exchange': 'Binance', 'instrument_id': 'ADA-USD', 'price': 0.845, 'timestamp': time.time()},

        # Spread aligns, triggering closing opportunity
        {'24h_volume': 18594708.87, 'best_ask': 0.846, 'best_bid': 0.846, 'exchange': 'Bybit', 'instrument_id': 'ADA-USD', 'price': 0.846, 'timestamp': time.time()},
        {'24h_volume': 19000000, 'best_ask': 0.8465, 'best_bid': 0.8465, 'exchange': 'Binance', 'instrument_id': 'ADA-USD', 'price': 0.8465, 'timestamp': time.time()},
    ]

    # Process each message
    for message in messages:
        print(f"Processing message: {message}")
        processor.process_message(message)

    # Show final balances and positions
    for exchange, simulator in simulators.items():
        print(f"Exchange: {exchange}")
        print(f"  Actual Balance: {simulator.actual_balance}")
        print(f"  Loaned Balance: {simulator.loaned_balance}")
        print(f"  Positions: {simulator.positions}")
        print(f"  Orders: {simulator.orders}")

if __name__ == "__main__":
    main()
