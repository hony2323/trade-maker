from datetime import datetime
from src.trading.exchanges.simulated_exchange import SimulatedExchange
from src.trading.arbitrage_detector import ArbitrageDetector
from src.trading.message_proccesor import MessageProcessor


def main():
    # Initialize exchanges with initial funds
    initial_funds = {"USD": 1000}
    coinbase = SimulatedExchange("coinbase", initial_funds=initial_funds, persist=True)
    bybit = SimulatedExchange("bybit", initial_funds=initial_funds, persist=True)
    kraken = SimulatedExchange("kraken", initial_funds=initial_funds, persist=True)

    # Create ArbitrageDetector
    simulators = {"coinbase": coinbase, "bybit": bybit, "kraken": kraken}
    arbitrage_detector = ArbitrageDetector(simulators, threshold=0.5)

    # Create MessageProcessor
    processor = MessageProcessor(simulators, arbitrage_detector, base_trade_amount=10)

    # Perform a hard reset for all simulators (reset balances and persist)
    for name, simulator in simulators.items():
        simulator.hard_reset(initial_funds=initial_funds)
        print(f"[{name.capitalize()}] Hard reset complete.")

    # Simulated price feed messages
    messages = [
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "coinbase", "instrument_id": "BTC-USD",
         "price": 50000},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "bybit", "instrument_id": "BTC-USD",
         "price": 49500},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "kraken", "instrument_id": "BTC-USD",
         "price": 51000},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "coinbase", "instrument_id": "BTC-USD",
         "price": 50500},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "bybit", "instrument_id": "BTC-USD",
         "price": 50000},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "kraken", "instrument_id": "BTC-USD",
         "price": 50050},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "coinbase", "instrument_id": "BTC-USD",
         "price": 49800},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "bybit", "instrument_id": "BTC-USD",
         "price": 50200},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "kraken", "instrument_id": "BTC-USD",
         "price": 50000},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "coinbase", "instrument_id": "BTC-USD",
         "price": 50000},
        {"timestamp": int(datetime.utcnow().timestamp()), "exchange": "bybit", "instrument_id": "BTC-USD",
         "price": 50001},
    ]

    # Process each message
    for msg in messages:
        processor.process_message(msg)

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
