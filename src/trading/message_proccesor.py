class MessageProcessor:
    def __init__(self, simulators, arbitrage_detector, base_trade_amount=10):
        self.simulators = simulators
        self.arbitrage_detector = arbitrage_detector
        self.base_trade_amount = base_trade_amount

    def process_message(self, message):
        try:
            symbol = message["instrument_id"].replace("-", "/")
            self.arbitrage_detector.update_prices(message)

            opportunities = self.arbitrage_detector.detect_opportunity(symbol)
            if opportunities:
                for opportunity in opportunities:
                    if opportunity["type"] == "open":
                        self._execute_arbitrage(opportunity)
                    elif opportunity["type"] == "close":
                        self._close_position(opportunity)
            else:
                print(f"No opportunities for {symbol}.")
        except Exception as e:
            print(f"Error processing message: {e}")

    def _execute_arbitrage(self, opportunity):
        try:
            symbol = opportunity["symbol"]
            buy_exchange = opportunity["buy_exchange"]
            sell_exchange = opportunity["sell_exchange"]
            buy_price = opportunity["buy_price"]
            sell_price = opportunity["sell_price"]
            spread = opportunity["spread"]

            quote_amount = self.base_trade_amount * self.simulators[buy_exchange].leverage
            base_amount = quote_amount / buy_price

            buy_simulator = self.simulators[buy_exchange]
            sell_simulator = self.simulators[sell_exchange]

            buy_simulator.place_order(symbol, "buy", base_amount, buy_price)
            sell_simulator.place_order(symbol, "sell", base_amount, sell_price)

            print(f"Opened arbitrage: Buy on {buy_exchange} at {buy_price}, Sell on {sell_exchange} at {sell_price}, Spread: {spread:.2f}%")
        except Exception as e:
            print(f"Error executing arbitrage: {e}")

    def _close_position(self, opportunity):
        try:
            symbol = opportunity["symbol"]
            exchange = opportunity["exchange"]
            side = opportunity["side"]
            price = opportunity["price"]
            amount = opportunity["amount"]

            simulator = self.simulators[exchange]
            simulator.close_position(symbol, side, amount, price)

            print(f"Closed {side} position on {exchange}: {amount} {symbol} at {price}")
        except Exception as e:
            print(f"Error closing position: {e}")
