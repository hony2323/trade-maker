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

                # Use the base trade amount (in quote asset, e.g., USDT)
                quote_amount = self.base_trade_amount * self.simulators[buy_exchange].leverage
                self._execute_arbitrage(symbol, buy_exchange, buy_price, sell_exchange, sell_price, quote_amount)
            else:
                print(f"No arbitrage opportunity for {symbol}.")
        except Exception as e:
            print(f"Error processing message: {e}")

    def _execute_arbitrage(self, symbol, buy_exchange, buy_price, sell_exchange, sell_price, quote_amount):
        """
        Execute arbitrage trades on the given exchanges.
        :param symbol: Trading pair (e.g., "BTC/USDT").
        :param buy_exchange: Exchange to buy from.
        :param buy_price: Price on the buy exchange.
        :param sell_exchange: Exchange to sell on.
        :param sell_price: Price on the sell exchange.
        :param quote_amount: Amount of quote asset (e.g., USDT) to use for the trade.
        """
        try:
            buy_simulator = self.simulators[buy_exchange]
            sell_simulator = self.simulators[sell_exchange]

            # Calculate base asset amount
            base_amount = quote_amount / buy_price

            # Place buy (long) and sell (short) orders
            buy_simulator.place_order(symbol, side="buy", amount=base_amount, price=buy_price)
            sell_simulator.place_order(symbol, side="sell", amount=base_amount, price=sell_price)

            print(f"Opened arbitrage positions: {base_amount} {symbol}")
        except ValueError as e:
            print(f"Trade error: {e}")
        except Exception as e:
            print(f"Error executing arbitrage: {e}")
