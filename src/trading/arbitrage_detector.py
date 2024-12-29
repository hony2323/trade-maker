from collections import defaultdict, deque

class ArbitrageDetector:
    def __init__(self, simulators, threshold=0.5, alignment_threshold=0.01, history_size=5):
        self.simulators = simulators
        self.threshold = threshold
        self.alignment_threshold = alignment_threshold
        self.history_size = history_size
        self.price_state = defaultdict(lambda: defaultdict(deque))  # Exchange-symbol price history
        self.arbitrage_pairs = set()  # Track active arbitrage pairs

    def update_prices(self, message):
        exchange_name = message["exchange"]
        symbol = message["instrument_id"].replace("-", "/")
        price = message["price"]
        timestamp = message["timestamp"]

        if len(self.price_state[exchange_name][symbol]) >= self.history_size:
            self.price_state[exchange_name][symbol].popleft()
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
                pair_key = f"{buy_exchange}-{sell_exchange}"
                reverse_pair_key = f"{sell_exchange}-{buy_exchange}"
                spread = ((sell_price - buy_price) / buy_price) * 100

                # Check for existing positions and prevent duplicate trades
                if spread >= self.threshold and pair_key not in self.arbitrage_pairs and reverse_pair_key not in self.arbitrage_pairs:
                    opportunities.append({
                        "type": "open",
                        "symbol": symbol,
                        "buy_exchange": buy_exchange,
                        "buy_price": buy_price,
                        "sell_exchange": sell_exchange,
                        "sell_price": sell_price,
                        "spread": spread,
                    })
                    self.arbitrage_pairs.add(pair_key)

        # Detect opportunities to close matching positions across exchanges
        for buy_exchange, buy_price in prices.items():
            for sell_exchange, sell_price in prices.items():
                if buy_exchange == sell_exchange:
                    continue
                pair_key = f"{buy_exchange}-{sell_exchange}"
                if pair_key in self.arbitrage_pairs:
                    buy_simulator = self.simulators[buy_exchange]
                    sell_simulator = self.simulators[sell_exchange]
                    if (symbol in buy_simulator.positions and buy_simulator.positions[symbol]["long"] > 0 and
                            symbol in sell_simulator.positions and sell_simulator.positions[symbol]["short"] > 0):
                        # Check if prices align within the threshold
                        if abs((buy_price - sell_price) / sell_price) * 100 <= self.alignment_threshold:
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
                                ),
                                "pair_key": pair_key,
                            })

        return opportunities if opportunities else None
