from collections import defaultdict, deque

class ArbitrageDetector:
    def __init__(self, simulators, threshold=0.5, history_size=5):
        """
        Initialize the arbitrage detector with its own price state.
        :param simulators: Dictionary of simulators for each exchange.
        :param threshold: Minimum price difference (in %) to trigger arbitrage.
        :param history_size: Number of recent price updates to keep in memory.
        """
        self.simulators = simulators  # {"exchange_name": SimulatedExchange}
        self.threshold = threshold
        self.history_size = history_size
        self.price_state = defaultdict(lambda: defaultdict(deque))  # {exchange: {symbol: deque(prices)}}

    def update_prices(self, message):
        """
        Update in-memory price state with the latest message data.
        :param message: Trading data containing price and exchange details.
        """
        exchange_name = message["exchange"]
        symbol = message["instrument_id"].replace("-", "/")
        price = message["price"]
        timestamp = message["timestamp"]

        # Update the in-memory state
        if len(self.price_state[exchange_name][symbol]) >= self.history_size:
            self.price_state[exchange_name][symbol].popleft()  # Remove oldest price
        self.price_state[exchange_name][symbol].append({"price": price, "timestamp": timestamp})

    def detect_opportunity(self, symbol):
        prices = {}
        for exchange_name, symbols in self.price_state.items():
            if symbol in symbols and symbols[symbol]:
                prices[exchange_name] = symbols[symbol][-1]["price"]

        if len(prices) < 2:
            return None

        opportunities = []

        # Detect arbitrage opportunities for opening positions
        for buy_exchange, buy_price in prices.items():
            for sell_exchange, sell_price in prices.items():
                if buy_exchange == sell_exchange:
                    continue
                spread = ((sell_price - buy_price) / buy_price) * 100
                if spread >= self.threshold:
                    buy_simulator = self.simulators[buy_exchange]
                    sell_simulator = self.simulators[sell_exchange]
                    if (buy_simulator.positions[symbol]["long"] == 0 and
                            sell_simulator.positions[symbol]["short"] == 0):
                        opportunities.append({
                            "type": "open",
                            "symbol": symbol,
                            "buy_exchange": buy_exchange,
                            "buy_price": buy_price,
                            "sell_exchange": sell_exchange,
                            "sell_price": sell_price,
                            "spread": spread,
                        })

        # Detect opportunities to close positions
        for exchange_name, simulator in self.simulators.items():
            if symbol in simulator.positions:
                position = simulator.positions[symbol]
                if position["long"] > 0:  # Close long position
                    sell_price = prices.get(exchange_name)
                    if sell_price:
                        opportunities.append({
                            "type": "close",
                            "symbol": symbol,
                            "exchange": exchange_name,
                            "side": "long",
                            "price": sell_price,
                            "amount": position["long"],
                        })
                if position["short"] > 0:  # Close short position
                    buy_price = prices.get(exchange_name)
                    if buy_price:
                        opportunities.append({
                            "type": "close",
                            "symbol": symbol,
                            "exchange": exchange_name,
                            "side": "short",
                            "price": buy_price,
                            "amount": position["short"],
                        })

        return opportunities if opportunities else None
