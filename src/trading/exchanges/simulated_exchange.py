import uuid
from datetime import datetime
from collections import defaultdict


class SimulatedExchange:
    def __init__(self, exchange_name, initial_funds=None, fee_rate=0.001, leverage=10):
        """
        Initialize the simulated exchange with margin trading.
        :param exchange_name: Name of the exchange.
        :param initial_funds: Initial balances, e.g., {'USDT': 10000}.
        :param fee_rate: Trading fee rate as a decimal, e.g., 0.001 for 0.1%.
        :param leverage: Leverage multiplier, e.g., 10 for 10x leverage.
        """
        self.exchange_name = exchange_name
        self.real_balance = defaultdict(float, initial_funds or {})
        self.loaned_balance = defaultdict(float)  # Tracks loaned funds
        self.positions = defaultdict(lambda: {"long": 0, "short": 0})  # Track open positions
        self.fee_rate = fee_rate
        self.leverage = leverage

    def get_balance(self):
        """
        Return the current balances, including real and loaned funds.
        :return: Dictionary of real and loaned balances.
        """
        return {
            "real_balance": dict(self.real_balance),
            "loaned_balance": dict(self.loaned_balance),
        }

    def get_fee(self, amount, price):
        """
        Calculate the trading fee.
        :param amount: Amount being traded.
        :param price: Price per unit.
        :return: Fee as a float.
        """
        return amount * price * self.fee_rate

    def place_order(self, symbol, side, amount, price):
        """
        Place an order with margin trading support.
        :param symbol: Trading pair, e.g., 'BTC/USDT'.
        :param side: 'buy' (long) or 'sell' (short).
        :param amount: Order size.
        :param price: Current market price.
        """
        base_asset, quote_asset = symbol.split('/')
        margin_cost = (price * amount) / self.leverage
        fee = self.get_fee(amount, price)
        total_cost = margin_cost + fee

        if side == 'buy':  # Long position
            if self.real_balance[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance for margin.")
            self.real_balance[quote_asset] -= total_cost
            self.loaned_balance[base_asset] += amount
            self.positions[symbol]["long"] += amount

        elif side == 'sell':  # Short position
            if self.real_balance[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance for margin.")
            self.real_balance[quote_asset] -= total_cost
            self.loaned_balance[quote_asset] += margin_cost
            self.positions[symbol]["short"] += amount

    def close_position(self, symbol, side, amount, price):
        """
        Close an open position.
        :param symbol: Trading pair, e.g., 'BTC/USDT'.
        :param side: 'long' or 'short'.
        :param amount: Amount to close.
        :param price: Current market price.
        :return: Dictionary of the closing details.
        """
        if symbol not in self.positions:
            raise ValueError(f"No open positions for symbol {symbol}.")
        if side not in self.positions[symbol] or self.positions[symbol][side] < amount:
            raise ValueError(f"Not enough {side} position to close {amount} {symbol}.")

        base_asset, quote_asset = symbol.split('/')
        pnl = 0

        # Adjust balances and calculate profit/loss
        if side == 'long':
            self.positions[symbol]["long"] -= amount
            self.loaned_balance[base_asset] -= amount
            pnl = (price * amount) - (price * amount / self.leverage) - self.get_fee(amount, price)
            self.real_balance[quote_asset] += pnl
        elif side == 'short':
            self.positions[symbol]["short"] -= amount
            self.loaned_balance[quote_asset] -= amount * price
            pnl = (price * amount / self.leverage) - (price * amount) - self.get_fee(amount, price)
            self.real_balance[quote_asset] += pnl

        return {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            'closed_at': datetime.utcnow(),
        }
