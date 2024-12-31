from src.logger import logger


class ArbitrageDetector:
    def __init__(self, spread_threshold, alignment_threshold):
        self.spread_threshold = spread_threshold
        self.alignment_threshold = alignment_threshold
        self.prices = {}  # e.g., {'ADA-USD': {'Bybit': 0.8482, 'Binance': 0.845}}

    def update_price(self, exchange, symbol, price):
        """Update the latest price for a symbol on an exchange."""
        logger.debug(f"Updating price for {symbol} on {exchange}: {price}")
        if symbol not in self.prices:
            self.prices[symbol] = {}
        self.prices[symbol][exchange] = price

    def detect_opportunity(self, symbol, latest_exchange):
        """
        Detect arbitrage opportunities for a symbol, focusing on the latest exchange update.
        Returns a list of all opportunities.
        """
        if symbol not in self.prices or len(self.prices[symbol]) < 2:
            logger.debug(f"No arbitrage opportunities for {symbol}: insufficient exchanges.")
            return []

        latest_price = self.prices[symbol][latest_exchange]
        opportunities = []

        for exchange, price in self.prices[symbol].items():
            if exchange == latest_exchange:
                continue

            spread = abs(latest_price - price)
            if spread >= self.spread_threshold:
                if latest_price > price:
                    opportunities.append({
                        'symbol': symbol,
                        'short': {'exchange': latest_exchange, 'price': latest_price},
                        'long': {'exchange': exchange, 'price': price},
                        'spread': spread,
                    })
                else:
                    opportunities.append({
                        'symbol': symbol,
                        'short': {'exchange': exchange, 'price': price},
                        'long': {'exchange': latest_exchange, 'price': latest_price},
                        'spread': spread,
                    })

        logger.info(f"Detected {len(opportunities)} opportunities for {symbol}: {opportunities}")
        return opportunities

    def detect_closing_opportunity(self, open_positions):
        """Detect closing opportunities."""
        closing_opportunities = []
        for position in open_positions:
            symbol = position['symbol']
            short_exchange = position['short']['exchange']
            long_exchange = position['long']['exchange']

            short_price = self.prices[symbol].get(short_exchange)
            long_price = self.prices[symbol].get(long_exchange)

            if short_price is None or long_price is None:
                continue

            spread = abs(short_price - long_price)
            if spread <= self.alignment_threshold:
                logger.info(f"Closing opportunity detected: {position}")
                closing_opportunities.append(position)

        return closing_opportunities

    def get_prices_for_exchange(self, exchange):
        """
        Get all prices for a specific exchange.

        Args:
            exchange (str): The name of the exchange to fetch prices for.

        Returns:
            dict: A dictionary of symbols and their corresponding prices on the specified exchange.
        """
        exchange_prices = {
            symbol: exchanges[exchange]
            for symbol, exchanges in self.prices.items()
            if exchange in exchanges
        }
        logger.debug(f"Prices for exchange {exchange}: {exchange_prices}")
        return exchange_prices
