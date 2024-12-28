class MessageProcessor:
    def __init__(self, simulators, arbitrage_detector, base_trade_amount=100):
        """
        Initialize the message processor.
        :param simulators: Dictionary of simulators for each exchange.
        :param arbitrage_detector: Instance of ArbitrageDetector.
        :param base_trade_amount: Trade amount in USD before applying leverage.
        """
        self.simulators = simulators  # {"coinbase": SimulatedExchange, "bybit": SimulatedExchange, ...}
        self.arbitrage_detector = arbitrage_detector
        self.base_trade_amount = base_trade_amount  # USD before leverage

    def process_message(self, message):
        """
        Process a single message, detect arbitrage opportunities, and execute trades.
        :param message: Trading data (normalized).
        """
        try:
            symbol = message["instrument_id"].replace("-", "/")
            self.arbitrage_detector.update_prices(message)

            # Detect arbitrage opportunity
            opportunity = self.arbitrage_detector.detect_opportunity(symbol)
            if opportunity:
                buy_exchange, sell_exchange, spread = opportunity
                print(f"Arbitrage opportunity detected: {spread:.2f}%")
                trade_amount = self.base_trade_amount / self.simulators[buy_exchange].leverage
                self._execute_arbitrage(symbol, buy_exchange, sell_exchange, trade_amount)
            else:
                print(f"No arbitrage opportunity for {symbol}.")
        except Exception as e:
            print(f"Error processing message: {e}")

    def _execute_arbitrage(self, symbol, buy_exchange, sell_exchange, amount):
        """
        Execute arbitrage trades on the given exchanges.
        :param symbol: Trading pair (e.g., "BTC/USDT").
        :param buy_exchange: Exchange to buy from.
        :param sell_exchange: Exchange to sell on.
        :param amount: Amount to trade.
        """
        try:
            buy_simulator = self.simulators[buy_exchange]
            sell_simulator = self.simulators[sell_exchange]

            # Place buy and sell orders
            buy_price = buy_simulator.balances[symbol]
            sell_price = sell_simulator.balances[symbol]

            buy_order = buy_simulator.place_order(symbol, side="buy", amount=amount, price=buy_price)
            sell_order = sell_simulator.place_order(symbol, side="sell", amount=amount, price=sell_price)

            # Calculate and log profit
            profit = (sell_price - buy_price) * amount - (buy_order["fee"] + sell_order["fee"])
            print(f"Arbitrage trade executed: Profit = {profit:.2f} {symbol.split('/')[1]}")

        except Exception as e:
            print(f"Error executing arbitrage: {e}")
