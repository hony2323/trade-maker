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
                buy_exchange, buy_price, sell_exchange, sell_price, spread = opportunity
                print(f"Arbitrage opportunity detected: {spread:.2f}%")
                trade_amount = self.base_trade_amount / self.simulators[buy_exchange].leverage
                self._execute_arbitrage(symbol, buy_exchange, buy_price, sell_exchange, sell_price, trade_amount)
            else:
                print(f"No arbitrage opportunity for {symbol}.")
        except Exception as e:
            print(f"Error processing message: {e}")

    def _execute_arbitrage(self, symbol, buy_exchange, buy_price, sell_exchange, sell_price, amount):
        """
        Execute arbitrage trades on the given exchanges.
        :param symbol: Trading pair (e.g., "BTC/USDT").
        :param buy_exchange: Exchange to buy from.
        :param buy_price: Price on the buy exchange.
        :param sell_exchange: Exchange to sell on.
        :param sell_price: Price on the sell exchange.
        :param amount: Amount to trade.
        """
        try:
            buy_simulator = self.simulators[buy_exchange]
            sell_simulator = self.simulators[sell_exchange]

            # Place buy order
            buy_order = buy_simulator.place_order(symbol, side="buy", amount=amount, price=buy_price, order_type="market")

            # Place sell order
            sell_order = sell_simulator.place_order(symbol, side="sell", amount=amount, price=sell_price, order_type="market")

            # Calculate and log profit
            profit = (sell_price - buy_price) * amount - (buy_order["fee"] + sell_order["fee"])
            print(f"Arbitrage trade executed: Profit = {profit:.2f} {symbol.split('/')[1]}")

        except ValueError as e:
            print(f"Trade error: {e}")
        except Exception as e:
            print(f"Error executing arbitrage: {e}")
