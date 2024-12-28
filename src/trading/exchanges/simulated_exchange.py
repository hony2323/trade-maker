import uuid
from datetime import datetime
from collections import defaultdict


class SimulatedExchange:
    def __init__(self, initial_balances=None, fee_rate=0.001):
        """
        Initialize the simulated exchange.
        :param initial_balances: Dictionary of initial balances, e.g., {'BTC': 1.0, 'USDT': 10000}.
        :param fee_rate: Trading fee as a decimal (default: 0.001 = 0.1%).
        """
        self.balances = initial_balances or defaultdict(float)
        self.orders = []
        self.fee_rate = fee_rate

    def get_balance(self):
        """
        Return the current balances.
        :return: Dictionary of balances.
        """
        return dict(self.balances)

    def get_fee(self, symbol, order_type, amount):
        """
        Calculate the trading fee for a given order.
        :param symbol: Trading pair (e.g., 'BTC/USDT').
        :param order_type: 'market' or 'limit'.
        :param amount: The amount being traded.
        :return: Calculated fee.
        """
        # For simplicity, fees are proportional to the trade amount
        return amount * self.fee_rate

    def place_order(self, symbol, side, order_type, amount, price=None):
        """
        Simulate placing an order.
        :param symbol: Trading pair (e.g., 'BTC/USDT').
        :param side: 'buy' or 'sell'.
        :param order_type: 'market' or 'limit'.
        :param amount: Order size.
        :param price: Optional; price for limit orders.
        :return: Dictionary representing the order details.
        """
        # Check if sufficient balance exists for the trade
        base_asset, quote_asset = symbol.split('/')
        if side == 'buy':
            required_balance = (price or 1) * amount
            if self.balances[quote_asset] < required_balance:
                raise ValueError(f"Insufficient {quote_asset} balance to place buy order.")
        elif side == 'sell':
            if self.balances[base_asset] < amount:
                raise ValueError(f"Insufficient {base_asset} balance to place sell order.")

        # Create a new order
        order = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'amount': amount,
            'price': price,
            'status': 'open',
            'created_at': datetime.utcnow(),
        }
        self.orders.append(order)

        # Simulate immediate market fills
        if order_type == 'market':
            self._execute_order(order)

        return order

    def _execute_order(self, order):
        """
        Execute an order immediately (used for market orders).
        :param order: The order to execute.
        """
        base_asset, quote_asset = order['symbol'].split('/')
        amount = order['amount']
        price = order['price'] or 1  # Market price is assumed as 1 for simplicity
        fee = self.get_fee(order['symbol'], order['type'], amount)

        # Ensure assets exist in balances
        self.balances.setdefault(base_asset, 0)
        self.balances.setdefault(quote_asset, 0)

        if order['side'] == 'buy':
            cost = amount * price
            if self.balances[quote_asset] < cost + fee:
                raise ValueError(f"Insufficient {quote_asset} balance to execute buy order.")
            self.balances[quote_asset] -= cost + fee
            self.balances[base_asset] += amount
        elif order['side'] == 'sell':
            if self.balances[base_asset] < amount:
                raise ValueError(f"Insufficient {base_asset} balance to execute sell order.")
            self.balances[base_asset] -= amount
            self.balances[quote_asset] += (amount * price) - fee

        order['status'] = 'filled'
        order['filled_at'] = datetime.utcnow()

    def cancel_order(self, order_id):
        """
        Cancel an active order.
        :param order_id: The ID of the order to cancel.
        """
        for order in self.orders:
            if order['id'] == order_id and order['status'] == 'open':
                order['status'] = 'canceled'
                order['canceled_at'] = datetime.utcnow()
                return order
        raise ValueError("Order not found or already closed.")

    def update_order_status(self):
        """
        Update the status of limit orders (simulate fills or partial fills).
        """
        for order in self.orders:
            if order['status'] == 'open' and order['type'] == 'limit':
                # Simulate random fills (for demonstration purposes)
                order['status'] = 'filled'
                order['filled_at'] = datetime.utcnow()
                self._execute_order(order)

    def get_orders(self, status=None):
        """
        Retrieve orders by status.
        :param status: Optional; filter by status (e.g., 'open', 'filled').
        :return: List of orders matching the status.
        """
        if status:
            return [order for order in self.orders if order['status'] == status]
        return self.orders
