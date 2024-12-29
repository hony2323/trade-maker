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
        """
        Detect arbitrage opportunities for a given trading pair.
        :param symbol: Trading pair (e.g., "BTC/USDT").
        :return: Tuple (buy_exchange, buy_price, sell_exchange, sell_price, spread) or None.
        """
        prices = {}
        for exchange_name, symbols in self.price_state.items():
            if symbol in symbols and symbols[symbol]:
                prices[exchange_name] = symbols[symbol][-1]["price"]  # Latest price

        if len(prices) < 2:
            return None  # Not enough exchanges for arbitrage

        # Find the lowest and highest price
        buy_exchange = min(prices, key=prices.get)
        sell_exchange = max(prices, key=prices.get)
        buy_price = prices[buy_exchange]
        sell_price = prices[sell_exchange]
        spread = ((sell_price - buy_price) / buy_price) * 100

        if spread >= self.threshold:
            return buy_exchange, buy_price, sell_exchange, sell_price, spread
        return None
