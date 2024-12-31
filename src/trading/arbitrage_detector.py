class ArbitrageDetector:
    def __init__(self, spread_threshold, alignment_threshold):
        self.spread_threshold = spread_threshold
        self.alignment_threshold = alignment_threshold
        self.prices = {}  # e.g., {'ADA-USD': {'Bybit': 0.8482, 'Binance': 0.845}}

    def update_price(self, exchange, symbol, price):
        """Update the latest price for a symbol on an exchange."""
        if symbol not in self.prices:
            self.prices[symbol] = {}
        self.prices[symbol][exchange] = price

    def detect_opportunity(self, symbol, latest_exchange):
        """
        Detect arbitrage opportunities for a symbol, focusing on the latest exchange update.
        """
        if symbol not in self.prices or len(self.prices[symbol]) < 2:
            return None

        # Find the latest price from the updated exchange
        latest_price = self.prices[symbol][latest_exchange]
        opportunities = []

        # Compare with all other exchanges for the same symbol
        for exchange, price in self.prices[symbol].items():
            if exchange == latest_exchange:
                continue

            # Determine if there's an arbitrage opportunity
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

        # Return the first detected opportunity (or refine logic to pick the best one)
        return opportunities[0] if opportunities else None

    def detect_closing_opportunity(self, open_positions):
        """
        Detect opportunities to close counter positions based on alignment threshold.
        """
        closing_opportunities = []
        for position in open_positions:
            symbol = position['symbol']
            short_exchange = position['short']['exchange']
            long_exchange = position['long']['exchange']

            if symbol not in self.prices:
                continue

            # Get the latest prices for the involved exchanges
            short_price = self.prices[symbol].get(short_exchange)
            long_price = self.prices[symbol].get(long_exchange)

            if short_price is None or long_price is None:
                continue

            # Check if the spread has collapsed within the alignment threshold
            spread = abs(short_price - long_price)
            if spread <= self.alignment_threshold:
                closing_opportunities.append(position)

        return closing_opportunities
