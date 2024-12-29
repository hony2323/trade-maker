from collections import defaultdict, deque

class ArbitrageDetector:
    def __init__(self, simulators, threshold=0.5, alignment_threshold=0.01, history_size=5):
        """
        Initialize the arbitrage detector.
        :param simulators: Dictionary of simulators for each exchange.
        :param threshold: Minimum profit percentage to trigger opening opportunities.
        :param alignment_threshold: Maximum price difference (in %) to trigger closing opportunities.
        :param history_size: Number of recent price updates to store.
        """
        self.simulators = simulators
        self.threshold = threshold
        self.alignment_threshold = alignment_threshold
        self.history_size = history_size
        self.price_state = defaultdict(lambda: defaultdict(deque))  # Exchange-symbol price history

    def update_prices(self, message):
        """
        Update the in-memory price state with the latest message data.
        """
        exchange_name = message["exchange"]
        symbol = message["instrument_id"].replace("-", "/")
        price = message["price"]
        timestamp = message["timestamp"]

        if len(self.price_state[exchange_name][symbol]) >= self.history_size:
            self.price_state[exchange_name][symbol].popleft()
        self.price_state[exchange_name][symbol].append({"price": price, "timestamp": timestamp})

    def detect_opportunity(self, symbol):
        """
        Detect arbitrage opportunities for opening or closing positions.
        :param symbol: Trading pair (e.g., "BTC/USDT").
        :return: List of opportunities to act on.
        """
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

        # Detect opportunities to close matching positions across exchanges
        for buy_exchange, buy_price in prices.items():
            for sell_exchange, sell_price in prices.items():
                if buy_exchange == sell_exchange:
                    continue
                buy_simulator = self.simulators[buy_exchange]
                sell_simulator = self.simulators[sell_exchange]
                if (symbol in buy_simulator.positions and buy_simulator.positions[symbol]["long"] > 0 and
                        symbol in sell_simulator.positions and sell_simulator.positions[symbol]["short"] > 0):
                    # Check if prices align within the threshold
                    if abs((buy_price - sell_price) / sell_price) <= self.alignment_threshold:
                        opportunities.append({
                            "type": "close",
                            "symbol": symbol,
                            "buy_exchange": buy_exchange,
                            "buy_price": buy_price,
                            "sell_exchange": sell_exchange,
                            "sell_price": sell_price,
                            "amount": min(
                                buy_simulator.positions[symbol]["long"],
                                sell_simulator.positions[symbol]["short"]
                            )
                        })

        return opportunities if opportunities else None
