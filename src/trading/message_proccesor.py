class MessageProcessor:
    def __init__(self, simulators, arbitrage_detector, base_trade_amount=10):
        self.simulators = simulators
        self.arbitrage_detector = arbitrage_detector
        self.base_trade_amount = base_trade_amount

    def process_message(self, message):
        try:
            # print(f"Processing message: {message}")
            symbol = message["instrument_id"].replace("-", "/")
            self.arbitrage_detector.update_prices(message)

            opportunities = self.arbitrage_detector.detect_opportunity(symbol)
            if opportunities:
                for opportunity in opportunities:
                    if opportunity["type"] == "open":
                        self._execute_arbitrage(opportunity)
                    elif opportunity["type"] == "close":
                        self._close_positions(opportunity)
            else:
                # print(f"No opportunities for {symbol}.")
                pass
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

            buy_simulator.place_order(symbol, side="buy", amount=base_amount, price=buy_price)
            sell_simulator.place_order(symbol, side="sell", amount=base_amount, price=sell_price)

            print(f"Opened arbitrage: Long on {buy_exchange} at {buy_price}, Short on {sell_exchange} at {sell_price}, Spread: {spread:.2f}% for {symbol}")
        except Exception as e:
            print(f"Error executing arbitrage: {e}")

    def _close_positions(self, opportunity):
        try:
            symbol = opportunity["symbol"]
            buy_exchange = opportunity["buy_exchange"]
            sell_exchange = opportunity["sell_exchange"]
            buy_price = opportunity["buy_price"]
            sell_price = opportunity["sell_price"]
            amount = opportunity["amount"]
            pair_key = opportunity["pair_key"]

            buy_simulator = self.simulators[buy_exchange]
            sell_simulator = self.simulators[sell_exchange]

            # Close the long and short positions
            buy_result = buy_simulator.close_position(symbol, "long", amount, buy_price)
            sell_result = sell_simulator.close_position(symbol, "short", amount, sell_price)

            # Extract individual PnL and entry prices
            pnl1 = buy_result["pnl"]
            pnl2 = sell_result["pnl"]
            total_pnl = pnl1 + pnl2
            buy_entry_price = buy_simulator.positions[symbol]["long_entry_price"]
            sell_entry_price = sell_simulator.positions[symbol]["short_entry_price"]

            # Print summary
            print(
                f"Closed positions: Long on {buy_exchange} (Entry: {buy_entry_price}, Close: {buy_price}) "
                f"and Short on {sell_exchange} (Entry: {sell_entry_price}, Close: {sell_price}), "
                f"Amount: {amount} {symbol}, "
                f"PnL: Long = {pnl1:.2f}, Short = {pnl2:.2f}, Total = {total_pnl:.2f}"
            )

            # Remove the pair key from active arbitrage pairs
            self.arbitrage_detector.arbitrage_pairs.discard(pair_key)

            return total_pnl
        except Exception as e:
            print(f"Error closing positions: {e}")
            return None
