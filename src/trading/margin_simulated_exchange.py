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
        """Close part or all of a position."""
        if symbol not in self.positions:
            raise ValueError("No open position for the symbol.")

        position = self.positions[symbol]
        closed_pnl, fees = position.close(amount, price)

        # Update balances
        self.actual_balance += closed_pnl - fees
        self.loaned_balance -= min(amount, position.loaned_balance)  # Repay proportionally

        # Record order
        self.orders.append({
            'symbol': symbol,
            'side': 'close',
            'amount': amount,
            'price': price,
            'fee': fees,
            'timestamp': time.time(),
        })

        if position.is_empty():
            del self.positions[symbol]

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

class Position:
    def __init__(self, symbol):
        self.symbol = symbol
        self.amount = 0
        self.side = None
        self.entry_price = None
        self.leverage = None
        self.fees = 0
        self.loaned_balance = 0

    def add(self, amount, price, side, leverage, fees):
        self.amount += amount
        self.entry_price = price
        self.side = side
        self.leverage = leverage
        self.fees = fees

    def close(self, amount, price):
        if amount > self.amount:
            raise ValueError("Amount exceeds the position size.")

        # Calculate PnL
        pnl = (price - self.entry_price) * amount * (1 if self.side == 'long' else -1)
        fees = amount * self.fees

        # Update position
        self.amount -= amount
        self.fees += fees

        return pnl, fees

    def is_empty(self):
        return self.amount == 0

    def serialize(self):
        return {
            'symbol': self.symbol,
            'amount': self.amount,
            'side': self.side,
            'entry_price': self.entry_price,
            'leverage': self.leverage,
            'fees': self.fees,
            'loaned_balance': self.loaned_balance,
        }

    @staticmethod
    def deserialize(state):
        position = Position(state['symbol'])
        position.amount = state['amount']
        position.side = state['side']
        position.entry_price = state['entry_price']
        position.leverage = state['leverage']
        position.fees = state['fees']
        position.loaned_balance = state['loaned_balance']
        return position
