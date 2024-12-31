from src.logger import logger


class MessageProcessor:
    def __init__(self, simulators, arbitrage_detector, base_trade_amount=10):
        self.simulators = simulators
        self.arbitrage_detector = arbitrage_detector
        self.base_trade_amount = base_trade_amount
        self.position_tracker = {}

    def process_message(self, message):
        try:
            # print(f"Processing message: {message}")
            symbol = message["instrument_id"].replace("-", "/")
            exchange_name = message["exchange"]
            self.arbitrage_detector.update_prices(message)

            opportunities = self.arbitrage_detector.detect_opportunity(symbol, self.position_tracker)
            if opportunities:
                for opportunity in opportunities:
                    if opportunity["type"] == "open":
                        position = self._execute_arbitrage(opportunity)
                        self._save_position(position)

                    elif opportunity["type"] == "close":
                        self._close_positions(opportunity)
            else:
                # print(f"No opportunities for {symbol}.")
                pass
        except Exception as e:
            print(f"Error processing message: {e}")

    def _save_position(self, position):
        symbol = position["symbol"]
        buy_exchange = position["buy_exchange"]
        sell_exchange = position["sell_exchange"]
        amount = position["amount"]
        pair_key = position["pair_key"]
        self.position_tracker.setdefault(pair_key, {})[symbol] = {
            "buy_exchange": buy_exchange,
            "sell_exchange": sell_exchange,
            "amount": amount,
        }

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

            logger.info(
                f"Opened arbitrage: Long on {buy_exchange} at {buy_price}, Short on {sell_exchange} at {sell_price}, Spread: {spread:.2f}% for {symbol}")
            return {
                "symbol": symbol,
                "buy_exchange": buy_exchange,
                "sell_exchange": sell_exchange,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "amount": base_amount,
                "pair_key": f"{buy_exchange}-{sell_exchange}",
            }

        except Exception as e:
            print(f"Error executing arbitrage: {e}")
            raise e

    def _close_positions(self, opportunity):
        try:
            symbol = opportunity["symbol"]
            buy_exchange = opportunity["buy_exchange"]
            sell_exchange = opportunity["sell_exchange"]
            buy_price = opportunity["buy_price"]
            sell_price = opportunity["sell_price"]
            pair_key = opportunity["pair_key"]
            # amount = opportunity["amount"]
            amount = self.position_tracker.get(pair_key, {}).get(symbol, {}).get("amount")
            if not amount:
                logger.warn(f"Amount not found for {pair_key} and {symbol}")
                return

            buy_simulator = self.simulators[buy_exchange]
            sell_simulator = self.simulators[sell_exchange]

            # Close the long and short positions
            buy_result = buy_simulator.close_position(symbol, "long", amount, buy_price)
            sell_result = sell_simulator.close_position(symbol, "short", amount, sell_price)

            del self.position_tracker[pair_key][symbol]
            # Extract individual PnL and entry prices
            pnl1 = buy_result["pnl"]
            pnl2 = sell_result["pnl"]
            total_pnl = pnl1 + pnl2
            buy_entry_price = buy_result["entry_price"]
            sell_entry_price = sell_result["entry_price"]

            # Print summary
            logger.info(
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
