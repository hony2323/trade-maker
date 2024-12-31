import json
import os
from datetime import datetime
from collections import defaultdict

from src.logger import logger


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
            self.positions = defaultdict(lambda: {"long": 0, "short": 0, "long_entry_price": None, "short_entry_price": None})
            self.orders = []
            # makedirs
            os.makedirs(storage_dir, exist_ok=True)
            self._save_persistent_data()

    def get_balance(self):
        """
        Return the current balances, including real and loaned funds.
        """
        return {
            "real_balance": dict(self.real_balance),
            "loaned_balance": dict(self.loaned_balance),
            "positions": {symbol: {
                "long": data["long"],
                "short": data["short"],
                "long_entry_price": data["long_entry_price"],
                "short_entry_price": data["short_entry_price"],
            } for symbol, data in self.positions.items()},
        }

    def _save_persistent_data(self):
        if not self.persist:
            return
        state = {
            "real_balance": dict(self.real_balance),
            "loaned_balance": dict(self.loaned_balance),
            "positions": dict(self.positions),  # Save the updated structure
            "orders": self.orders,
        }
        with open(self.storage_file, "w") as file:
            json.dump(state, file, indent=4)

    def _load_persistent_data(self):
        with open(self.storage_file, "r") as file:
            state = json.load(file)
        self.real_balance = defaultdict(float, state.get("real_balance", {}))
        self.loaned_balance = defaultdict(float, state.get("loaned_balance", {}))
        self.positions = defaultdict(
            lambda: {"long": 0, "short": 0, "long_entry_price": None, "short_entry_price": None},
            state.get("positions", {})
        )
        self.orders = state.get("orders", [])

    def hard_reset(self, initial_funds=None):
        """
        Reset all balances and positions to their initial state.
        :param initial_funds: Dictionary of initial balances, e.g., {'USDT': 10000}.
        """
        self.real_balance = defaultdict(float, initial_funds or {})
        self.loaned_balance = defaultdict(float)
        self.positions = defaultdict(lambda: {"long": 0, "short": 0, "long_entry_price": None, "short_entry_price": None})
        self.orders = []
        self._save_persistent_data()
        logger.debug(f"[{self.exchange_name}] Hard reset performed. Balances set to initial state.")

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
                raise ValueError(f"Insufficient {quote_asset} balance for margin. balance: {self.real_balance[quote_asset]}, cost: {total_cost}")
            self.real_balance[quote_asset] -= total_cost
            self.positions[symbol]["long"] += amount
            if self.positions[symbol].get("long_entry_price") is None:
                self.positions[symbol]["long_entry_price"] = price  # Set entry price for long positions

        elif side == 'sell':  # Short position
            if self.real_balance[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance for margin. balance: {self.real_balance[quote_asset]}, cost: {total_cost}")
            self.real_balance[quote_asset] -= total_cost
            self.positions[symbol]["short"] += amount
            if self.positions[symbol].get("short_entry_price") is None:
                self.positions[symbol]["short_entry_price"] = price  # Set entry price for short positions
        self.orders += [{
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'fee': fee,
            'created_at': datetime.utcnow().isoformat(),
        }]
        self._save_persistent_data()

    def close_position(self, symbol, side, amount, price):
        if symbol not in self.positions:
            raise ValueError(f"No open positions for symbol {symbol}.")
        if side not in self.positions[symbol] or self.positions[symbol][side] < amount:
            raise ValueError(f"Not enough {side} position to close {amount} {symbol}.")

        base_asset, quote_asset = symbol.split('/')
        pnl = 0
        entry_price = None
        if side == 'long':
            entry_price = self.positions[symbol].get("long_entry_price")
            if not entry_price:
                raise ValueError(f"Entry price not set for long position in {symbol}.")

            self.positions[symbol]["long"] -= amount
            pnl = (price - entry_price) * amount - self.get_fee(amount, price)
            self.real_balance[quote_asset] += pnl + (entry_price * amount / self.leverage)

            # Clear entry price if the long position is fully closed
            if self.positions[symbol]["long"] == 0:
                self.positions[symbol]["long_entry_price"] = None

        elif side == 'short':
            entry_price = self.positions[symbol].get("short_entry_price")
            if not entry_price:
                raise ValueError(f"Entry price not set for short position in {symbol}.")

            self.positions[symbol]["short"] -= amount
            pnl = (entry_price - price) * amount - self.get_fee(amount, price)
            self.real_balance[quote_asset] += pnl + (entry_price * amount / self.leverage)

            # Clear entry price if the short position is fully closed
            if self.positions[symbol]["short"] == 0:
                self.positions[symbol]["short_entry_price"] = None
        self.orders += [{
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            'created_at': datetime.utcnow().isoformat(),
        }]
        self._save_persistent_data()

        return {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            "entry_price": entry_price,
            'closed_at': datetime.utcnow(),
        }
