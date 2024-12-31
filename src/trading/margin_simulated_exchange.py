import json
import time


class MarginTradingSimulator:
    def __init__(self, balance, fees, leverage_limit, storage_path):
        self.actual_balance = balance
        self.loaned_balance = 0
        self.positions = {}  # e.g., {'BTC/USDT': Position}
        self.orders = []  # List of order dictionaries
        self.fees = fees  # Dict: {'maker': 0.001, 'taker': 0.002, 'borrow': 0.0001}
        self.leverage_limit = leverage_limit
        self.storage_path = storage_path

    def open_position(self, symbol, side, amount, leverage, price):
        """Open a position with given leverage and price."""
        if leverage > self.leverage_limit:
            raise ValueError(f"Leverage {leverage} exceeds the limit of {self.leverage_limit}")

        # Calculate fees and initial margin
        margin_required = amount / leverage
        if margin_required > self.actual_balance:
            raise ValueError("Insufficient balance to open position.")

        maker_fee = amount * self.fees['maker'] if side == 'maker' else amount * self.fees['taker']
        borrow_fee = margin_required * self.fees['borrow']
        total_cost = margin_required + maker_fee + borrow_fee

        # Deduct from balance
        self.actual_balance -= margin_required
        self.loaned_balance += margin_required * (leverage - 1)

        # Record position
        position = self.positions.get(symbol, Position(symbol))
        position.add(amount, price, side, leverage, maker_fee + borrow_fee)
        self.positions[symbol] = position

        # Record order
        self.orders.append({
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'leverage': leverage,
            'fee': maker_fee + borrow_fee,
            'timestamp': time.time(),
        })

    def close_position(self, symbol, amount, price):
        """
        Close part or all of a position for a given symbol.
        """
        if symbol not in self.positions:
            raise ValueError(f"No open position for symbol {symbol}.")

        position = self.positions[symbol]

        # Determine the side to close (opposite of the current side)
        close_side = 'short' if position.side == 'long' else 'long'

        # Use the position's add method to handle the close logic
        realized_pnl = position.add(amount, price, close_side, position.leverage, fees=0)  # Fees handled within Position

        # Update account balances
        self.actual_balance += realized_pnl
        self.loaned_balance -= min(amount, position.loaned_balance)

        # Remove the position if fully closed
        if position.is_empty():
            del self.positions[symbol]

        return realized_pnl

    def save_state(self):
        """Persist the state to a file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self._serialize_state(), f, indent=4)

    def load_state(self):
        """Load state from a file."""
        with open(self.storage_path, 'r') as f:
            state = json.load(f)
            self._deserialize_state(state)

    def _serialize_state(self):
        return {
            'actual_balance': self.actual_balance,
            'loaned_balance': self.loaned_balance,
            'positions': {k: v.serialize() for k, v in self.positions.items()},
            'orders': self.orders,
        }

    def _deserialize_state(self, state):
        self.actual_balance = state['actual_balance']
        self.loaned_balance = state['loaned_balance']
        self.positions = {k: Position.deserialize(v) for k, v in state['positions'].items()}
        self.orders = state['orders']

    def close_all_positions(self, prices):
        """
        Close all open positions using the provided prices.

        Args:
            prices (dict): A dictionary of symbol-to-price mappings, e.g., {'BTC-USD': 32000, 'ETH-USD': 2500}.

        Returns:
            dict: A summary of closed positions with PnL for each symbol.
        """
        if not self.positions:
            raise ValueError("No open positions to close.")

        closed_positions = {}

        for symbol, position in list(self.positions.items()):  # Use list to allow modification during iteration
            if symbol not in prices:
                raise ValueError(f"No price provided for symbol {symbol}.")

            price = prices[symbol]

            # Close the position fully
            realized_pnl = position.add(amount=position.quote_amount, price=price, side='short' if position.side == 'long' else 'long', leverage=position.leverage, fees=0)

            # Update account balances
            self.actual_balance += realized_pnl
            self.loaned_balance -= min(position.quote_amount, position.loaned_balance)

            # Record the closed position
            closed_positions[symbol] = {
                'realized_pnl': realized_pnl,
                'final_price': price,
                'side': position.side,
            }

            # Remove the position after closing
            del self.positions[symbol]

        return closed_positions

class Position:
    def __init__(self, symbol):
        self.symbol = symbol
        self.quote_amount = 0  # Total quote currency amount
        self.base_amount = 0  # Total base currency amount
        self.side = None  # 'long' or 'short'
        self.avg_entry_price = None  # Weighted average entry price
        self.leverage = None  # Leverage used for the position
        self.fees = 0  # Total fees paid
        self.loaned_balance = 0  # Amount borrowed for leverage

    def add(self, amount, price, side, leverage, fees):
        """Add to the position, handling opposite side adjustments and PnL tracking."""
        realized_pnl = 0  # To track realized PnL from offsetting trades

        if self.side and self.side != side:
            # Opposite side addition (offset existing position)
            if amount > self.quote_amount:
                # Fully offset the current position and open a new one
                realized_pnl += (price - self.avg_entry_price) * self.quote_amount * (1 if self.side == 'long' else -1)
                self.reset()  # Fully close the current position
                remaining_amount = amount - self.quote_amount
                self.side = side
                self.quote_amount = remaining_amount
                self.avg_entry_price = price
                self.base_amount = self.quote_amount / price
            else:
                # Partially offset the current position
                realized_pnl += (price - self.avg_entry_price) * amount * (1 if self.side == 'long' else -1)
                self.quote_amount -= amount
                if self.quote_amount == 0:
                    self.reset()

            self.fees += fees
        else:
            # Same side addition
            if self.quote_amount > 0:
                total_cost = self.quote_amount * self.avg_entry_price + amount * price
                self.avg_entry_price = total_cost / (self.quote_amount + amount)
            else:
                self.avg_entry_price = price

            self.quote_amount += amount
            self.base_amount = self.quote_amount / self.avg_entry_price
            self.side = side
            self.leverage = leverage
            self.fees += fees

        return realized_pnl

    def close(self, amount, price):
        """Close part or all of the position."""
        if amount > self.quote_amount:
            raise ValueError("Amount exceeds the position size.")

        pnl = (price - self.avg_entry_price) * amount * (1 if self.side == 'long' else -1)
        fees = amount * (self.fees / self.quote_amount)

        self.quote_amount -= amount
        if self.quote_amount > 0:
            self.base_amount = self.quote_amount / self.avg_entry_price
        else:
            self.reset()

        self.fees -= fees
        return pnl, fees

    def reset(self):
        """Reset the position when it is fully closed."""
        self.quote_amount = 0
        self.base_amount = 0
        self.side = None
        self.avg_entry_price = None
        self.leverage = None

    def is_empty(self):
        """Check if the position is empty."""
        return self.quote_amount == 0

    def serialize(self):
        """Serialize the position to a dictionary."""
        return {
            'symbol': self.symbol,
            'quote_amount': self.quote_amount,
            'base_amount': self.base_amount,
            'side': self.side,
            'avg_entry_price': self.avg_entry_price,
            'leverage': self.leverage,
            'fees': self.fees,
            'loaned_balance': self.loaned_balance,
        }

    @staticmethod
    def deserialize(state):
        """Deserialize a dictionary into a Position object."""
        position = Position(state['symbol'])
        position.quote_amount = state['quote_amount']
        position.base_amount = state['base_amount']
        position.side = state['side']
        position.avg_entry_price = state['avg_entry_price']
        position.leverage = state['leverage']
        position.fees = state['fees']
        position.loaned_balance = state['loaned_balance']
        return position
