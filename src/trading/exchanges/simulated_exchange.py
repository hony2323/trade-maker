import uuid
import json
import os
from datetime import datetime
from collections import defaultdict


class SimulatedExchange:
    def __init__(self, exchange_name, initial_funds, storage_path="storage", fee_rate=0.001, leverage=10, liquidation_threshold=0.2):
        """
        Initialize the simulated exchange with margin trading support and persistence.
        :param exchange_name: Unique name of the exchange (e.g., 'coinbase', 'bybit').
        :param initial_funds: Dictionary of actual funds (e.g., {'USDT': 1000, 'BTC': 0.5}).
        :param storage_path: Path for persistent storage.
        :param fee_rate: Trading fee as a decimal (default: 0.001 = 0.1%).
        :param leverage: Maximum leverage allowed (default: 10x).
        :param liquidation_threshold: Margin level at which liquidation occurs (default: 20%).
        """
        self.exchange_name = exchange_name
        self.storage_path = storage_path
        self.fee_rate = fee_rate
        self.leverage = leverage
        self.liquidation_threshold = liquidation_threshold
        self.balances = defaultdict(float, initial_funds)
        self.orders = []
        self._load_persistent_data()

    def _get_storage_file(self):
        """Generate the file path for persistent storage."""
        return os.path.join(self.storage_path, f"{self.exchange_name}_data.json")

    def _load_persistent_data(self):
        """Load balances and orders from persistent storage."""
        os.makedirs(self.storage_path, exist_ok=True)
        storage_file = self._get_storage_file()
        if os.path.exists(storage_file):
            with open(storage_file, "r") as file:
                data = json.load(file)
                self.balances.update(data.get("balances", {}))
                self.orders = data.get("orders", [])

    def _save_persistent_data(self):
        """Save balances and orders to persistent storage."""
        storage_file = self._get_storage_file()
        data = {
            "balances": dict(self.balances),
            "orders": self.orders,
        }
        with open(storage_file, "w") as file:
            json.dump(data, file, indent=4)

    def get_balance(self):
        """Return the current balances."""
        return dict(self.balances)

    def place_order(self, symbol, side, amount, price):
        """
        Place a leveraged order and adjust balances accordingly.
        :param symbol: Trading pair (e.g., 'BTC/USDT').
        :param side: 'buy' or 'sell'.
        :param amount: Amount to trade.
        :param price: Price of the trade.
        :return: Order details.
        """
        base_asset, quote_asset = symbol.split('/')
        cost = price * amount
        margin_cost = cost / self.leverage
        fee = self.get_fee(symbol, amount, price)

        if side == 'buy':
            if self.balances[quote_asset] < margin_cost + fee:
                raise ValueError(f"Insufficient {quote_asset} balance to place buy order.")
            self.balances[quote_asset] -= (margin_cost + fee)
            self.balances[base_asset] += amount
        elif side == 'sell':
            if self.balances[base_asset] < amount:
                raise ValueError(f"Insufficient {base_asset} balance to place sell order.")
            self.balances[base_asset] -= amount
            self.balances[quote_asset] += (cost - fee)

        # Create the order
        order = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'margin_cost': margin_cost,
            'fee': fee,
            'status': 'filled',  # Immediate fill for simplicity
            'created_at': datetime.utcnow().isoformat(),
        }
        self.orders.append(order)
        self._save_persistent_data()
        self.check_liquidation()
        return order

    def get_fee(self, symbol, amount, price):
        """Calculate the trading fee."""
        return price * amount * self.fee_rate

    def check_liquidation(self):
        """Check for liquidation conditions."""
        for asset, balance in self.balances.items():
            margin_used = sum(order['margin_cost'] for order in self.orders if order['status'] == 'filled')
            equity = sum(self.balances.values())  # Total equity across all assets
            margin_level = equity / margin_used if margin_used > 0 else float('inf')

            if margin_level < self.liquidation_threshold:
                print(f"Liquidating positions due to low margin level ({margin_level:.2f}).")
                self._liquidate_all()

    def _liquidate_all(self):
        """Liquidate all positions."""
        self.orders = []
        for asset in self.balances.keys():
            self.balances[asset] = 0
        self._save_persistent_data()

    def get_positions(self):
        """Retrieve current open positions."""
        return [order for order in self.orders if order['status'] == 'filled']
