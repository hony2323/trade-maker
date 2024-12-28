import base64
import json

import requests
import time
import hmac
import hashlib
from src.logger import logger


class KrakenFuturesTrading:
    def __init__(self, api_key, api_secret, sandbox=True):
        """
        Initialize Kraken Futures Trading instance.
        :param api_key: Kraken Futures API key.
        :param api_secret: Kraken Futures API secret.
        :param sandbox: Use sandbox environment if True.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://demo-futures.kraken.com' if sandbox else 'https://futures.kraken.com'

    def _sign(self, endpoint, data):
        """Generate Kraken API signature."""
        nonce = str(int(time.time() * 1000))
        post_data = json.dumps(data) if data else '{}'
        message = (nonce + post_data).encode()
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            (endpoint.encode() + hashlib.sha256(message).digest()),
            hashlib.sha512,
        ).digest()
        return base64.b64encode(signature).decode(), nonce

    def _private_request(self, endpoint, data=None):
        """
        Make a private API request.
        :param endpoint: The endpoint for the request (e.g., '/0/private/Balance').
        :param data: Payload for the request.
        :return: API response as a dictionary.
        """
        url = f"{self.base_url}{endpoint}"
        data = data or {}
        signature, nonce = self._sign(endpoint, data)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'API-Key': self.api_key,
            'API-Sign': signature,
        }
        data['nonce'] = nonce  # Add nonce to the payload
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Request Error: {e}")
            return None

    def get_tickers(self):
        """Fetch market tickers."""
        endpoint = '/derivatives/api/v3/tickers'
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching tickers: {e}")
            return None

    def place_order(self, symbol, side, size, limit_price=None):
        """
        Place a futures order.
        :param symbol: Trading symbol (e.g., 'PI_XBTUSD').
        :param side: 'buy' or 'sell'.
        :param size: Order size in contracts.
        :param limit_price: Optional; specify for limit orders.
        :return: API response as a dictionary.
        """
        endpoint = '/derivatives/api/v3/sendorder'
        order_data = {
            'orderType': 'lmt' if limit_price else 'mkt',
            'symbol': symbol,
            'side': side,
            'size': size,
        }
        if limit_price:
            order_data['limitPrice'] = limit_price
        return self._private_request(endpoint, data=order_data)

    def get_balance(self):
        """
        Fetch account balances from Kraken Futures API.
        :return: Dictionary containing account balances.
        """
        endpoint = '/derivatives/api/v3/accounts'
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'API-Key': self.api_key,
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None

    def get_open_orders(self):
        """
        Fetch open orders from Kraken Futures API.
        :return: Dictionary containing open orders.
        """
        endpoint = '/derivatives/api/v3/openorders'
        try:
            response = self._private_request(endpoint, method='GET')
            if response and 'openOrders' in response:
                return response['openOrders']
            else:
                logger.error(f"Unexpected response format for open orders: {response}")
                return None
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return None

    def get_order_history(self):
        """
        Fetch historical orders from Kraken Futures API.
        :return: Dictionary containing order history.
        """
        endpoint = '/derivatives/api/v3/historyorders'
        try:
            response = self._private_request(endpoint, method='GET')
            if response and 'historyOrders' in response:
                return response['historyOrders']
            else:
                logger.error(f"Unexpected response format for order history: {response}")
                return None
        except Exception as e:
            logger.error(f"Error fetching order history: {e}")
            return None
