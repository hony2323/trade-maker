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
        self.balances = defaultdict(float, initial_funds or {})
        self.orders = []
        self.positions = defaultdict(lambda: {"long": 0, "short": 0})  # Track positions per symbol
        self.fee_rate = fee_rate
        self.leverage = leverage

    def get_balance(self):
        """Return the current balances."""
        return dict(self.balances)

    def get_fee(self, amount, price):
        """
        Calculate the trading fee.
        :param amount: Amount being traded.
        :param price: Price per unit.
        :return: Fee as a float.
        """
        return amount * price * self.fee_rate

    def place_order(self, symbol, side, order_type, amount=None, quote_amount=None, price=1):
        """
        Place an order with margin trading support.
        :param symbol: Trading pair, e.g., 'BTC/USDT'.
        :param side: 'buy' (long) or 'sell' (short).
        :param order_type: 'market' or 'limit'.
        :param amount: Order size.
        :param quote_amount: Quote amount for market orders.
        :param price: Price per unit.
        :return: Order details as a dictionary.
        """
        base_asset, quote_asset = symbol.split('/')

        # Determine amount from quote_amount if provided
        if amount is None and quote_amount is None:
            raise ValueError("Either 'amount' or 'quote_amount' must be provided.")
        if amount is None:
            amount = quote_amount / price

        # Calculate margin requirement
        margin_cost = (price * amount) / self.leverage
        fee = self.get_fee(amount, price)
        total_cost = margin_cost + fee

        # Validate balances based on the type of trade
        if side == 'buy':  # Long position
            if self.balances[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance to place long order.")
        elif side == 'sell':  # Short position
            if self.balances[quote_asset] < total_cost:
                raise ValueError(f"Insufficient {quote_asset} balance to place short order.")

        # Create the order
        order = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'amount': amount,
            'price': price,
            'status': 'open',
            'margin_cost': margin_cost,
            'fee': fee,
            'created_at': datetime.utcnow(),
        }
        self.orders.append(order)

        # Simulate immediate execution for market orders
        if order_type == 'market':
            self._execute_order(order)

        return order

    def _execute_order(self, order):
        """
        Execute an order immediately.
        :param order: The order to execute.
        """
        base_asset, quote_asset = order['symbol'].split('/')
        amount = order['amount']
        price = order['price']
        fee = order['fee']
        margin_cost = order['margin_cost']

        if order['side'] == 'buy':  # Long position
            self.balances[quote_asset] -= margin_cost + fee
            self.positions[order['symbol']]["long"] += amount
        elif order['side'] == 'sell':  # Short position
            self.balances[quote_asset] -= margin_cost + fee
            self.positions[order['symbol']]["short"] += amount

        order['status'] = 'filled'
        order['filled_at'] = datetime.utcnow()

    def get_positions(self):
        """
        Retrieve open positions.
        :return: Dictionary of positions by symbol with long and short amounts.
        """
        return dict(self.positions)

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
            pnl = (price * amount) - ((price * amount) / self.leverage) - self.get_fee(amount, price)
            self.balances[quote_asset] += pnl
        elif side == 'short':
            self.positions[symbol]["short"] -= amount
            pnl = ((price * amount) / self.leverage) - (price * amount) - self.get_fee(amount, price)
            self.balances[quote_asset] += pnl

        return {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'pnl': pnl,
            'closed_at': datetime.utcnow(),
        }
