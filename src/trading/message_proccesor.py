class MessageProcessor:
    def __init__(self, simulators, arbitrage_detector):
        self.simulators = simulators  # Dict of simulators by exchange
        self.detector = arbitrage_detector
        self.open_positions = {}  # e.g., {'ADA-USD': {'Bybit-Binance': {...}}}

    def process_message(self, message):
        """Process a price update message."""
        exchange = message['exchange']
        symbol = message['instrument_id']
        price = message['price']

        # Update prices in the detector
        self.detector.update_price(exchange, symbol, price)

        # Check for arbitrage opportunities
        opportunity = self.detector.detect_opportunity(symbol, exchange)
        if opportunity:
            self.handle_opportunity(opportunity)

        # Check for closing opportunities
        closing_opportunities = self.detector.detect_closing_opportunity(self.get_open_positions(symbol))
        for opportunity in closing_opportunities:
            self.handle_closing(opportunity)

        # Save the state of all simulators
        self.save_state()

    def handle_opportunity(self, opportunity):
        """Open counter positions for an arbitrage opportunity."""
        symbol = opportunity['symbol']
        short = opportunity['short']
        long = opportunity['long']

        # Ensure no duplicate positions
        pair_key = f"{short['exchange']}-{long['exchange']}"
        if symbol in self.open_positions and pair_key in self.open_positions[symbol]:
            return  # Skip if position already exists

        # Open positions
        short_sim = self.simulators[short['exchange']]
        long_sim = self.simulators[long['exchange']]

        short_sim.open_position(symbol, 'short', 1, 1, short['price'])
        long_sim.open_position(symbol, 'long', 1, 1, long['price'])

        # Track open positions
        if symbol not in self.open_positions:
            self.open_positions[symbol] = {}
        self.open_positions[symbol][pair_key] = opportunity

    def handle_closing(self, opportunity):
        """Close counter positions for a closing opportunity."""
        symbol = opportunity['symbol']
        short = opportunity['short']
        long = opportunity['long']

        # Close positions
        short_sim = self.simulators[short['exchange']]
        long_sim = self.simulators[long['exchange']]

        short_sim.close_position(symbol, 1, short['price'])
        long_sim.close_position(symbol, 1, long['price'])

        # Remove from open positions
        pair_key = f"{short['exchange']}-{long['exchange']}"
        if symbol in self.open_positions and pair_key in self.open_positions[symbol]:
            del self.open_positions[symbol][pair_key]

    def save_state(self):
        """Save the state of all simulators."""
        for simulator in self.simulators.values():
            simulator.save_state()

    def get_open_positions(self, symbol):
        """Get open positions for a symbol."""
        return self.open_positions.get(symbol, {}).values()
