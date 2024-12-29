import json
import os
from datetime import datetime
from collections import defaultdict


class SimulatedExchange:
    def __init__(self, exchange_name, initial_funds=None, fee_rate=0.001, leverage=10, persist=False,
                 storage_dir="storage"):
        """
        Initialize the simulated exchange with margin trading.
        :param exchange_name: Name of the exchange.
        :param initial_funds: Initial balances, e.g., {'USDT': 10000}.
        :param fee_rate: Trading fee rate as a decimal, e.g., 0.001 for 0.1%.
        :param leverage: Leverage multiplier, e.g., 10 for 10x leverage.
        :param persist: Whether to persist balances and positions.
        """
        self.exchange_name = exchange_name
        self.fee_rate = fee_rate
        self.leverage = leverage
        self.persist = persist
        self.storage_file = os.path.join(storage_dir, f"{exchange_name}_state.json") if persist else None

        # Load persistent data or initialize with initial funds
        if self.persist and os.path.exists(self.storage_file):
            self._load_persistent_data()
        else:
            self.real_balance = defaultdict(float, initial_funds or {})
            self.loaned_balance = defaultdict(float)
            self.positions = defaultdict(lambda: {"long": 0, "short": 0})
            # makedirs
            os.makedirs(storage_dir, exist_ok=True)
            self._save_persistent_data()

    def get_balance(self):
        """
        Return the current balances, including real and loaned funds.
        :return: Dictionary of real and loaned balances.
        """
        return {
            "real_balance": dict(self.real_balance),
            "loaned_balance": dict(self.loaned_balance),
        }

    def _save_persistent_data(self):
        """
        Save current state to a persistent storage file.
        """
        if not self.persist:
            return
        state = {
            "real_balance": dict(self.real_balance),
            "loaned_balance": dict(self.loaned_balance),
            "positions": dict(self.positions),
        }
        with open(self.storage_file, "w") as file:
            json.dump(state, file, indent=4)

    def _load_persistent_data(self):
        """
        Load state from a persistent storage file.
        """
        with open(self.storage_file, "r") as file:
            state = json.load(file)
        self.real_balance = defaultdict(float, state.get("real_balance", {}))
        self.loaned_balance = defaultdict(float, state.get("loaned_balance", {}))
        self.positions = defaultdict(lambda: {"long": 0, "short": 0}, state.get("positions", {}))

    def hard_reset(self, initial_funds=None):
        """
        Reset all balances and positions to their initial state.
        :param initial_funds: Dictionary of initial balances, e.g., {'USDT': 10000}.
        """
        self.real_balance = defaultdict(float, initial_funds or {})
        self.loaned_balance = defaultdict(float)
        self.positions = defaultdict(lambda: {"long": 0, "short": 0})
        self._save_persistent_data()
        print(f"[{self.exchange_name}] Hard reset performed. Balances set to initial state.")

    def get_fee(self, amount, price):
        """
        Calculate the trading fee.
        :param amount: Amount being traded.
        :param price: Price per unit.
        :return: Fee as a float.
        """
        return amount * price * self.fee_rate

    def place_order(self, symbol, side, amount, price):
        base_asset, quote_asset = symbol.split('/')
        margin_cost = (price * amount) / self.leverage
        fee = self.get_fee(amount, price)
        total_cost = margin_cost + fee

        if side == 'buy':  # Long position
            if self.real_balance[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance for margin.")
            self.real_balance[quote_asset] -= total_cost
            self.loaned_balance[base_asset] += amount * self.leverage
            self.positions[symbol]["long"] += amount
            self.positions[symbol]["entry_price"] = price  # Set entry price for long positions

        elif side == 'sell':  # Short position
            if self.real_balance[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance for margin.")
            self.real_balance[quote_asset] -= total_cost
            self.loaned_balance[quote_asset] += margin_cost * self.leverage
            self.positions[symbol]["short"] += amount
            self.positions[symbol]["entry_price"] = price  # Set entry price for short positions

        self._save_persistent_data()

    def close_position(self, symbol, side, amount, price):
        if symbol not in self.positions:
            raise ValueError(f"No open positions for symbol {symbol}.")
        if side not in self.positions[symbol] or self.positions[symbol][side] < amount:
            raise ValueError(f"Not enough {side} position to close {amount} {symbol}.")

        base_asset, quote_asset = symbol.split('/')
        pnl = 0
        entry_price = self.positions[symbol].get("entry_price")

        if not entry_price:
            raise ValueError(f"Entry price not set for {side} position in {symbol}.")

        if side == 'long':
            self.positions[symbol]["long"] -= amount
            loaned_amount = amount * entry_price
            self.loaned_balance[base_asset] -= loaned_amount
            pnl = (price * amount) - loaned_amount - self.get_fee(amount, price)
            self.real_balance[quote_asset] += pnl
        elif side == 'short':
            self.positions[symbol]["short"] -= amount
            loaned_amount = amount * entry_price
            self.loaned_balance[quote_asset] -= loaned_amount
            pnl = loaned_amount - (price * amount) - self.get_fee(amount, price)
            self.real_balance[quote_asset] += pnl

        self._save_persistent_data()

        return {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            'closed_at': datetime.utcnow(),
        }
