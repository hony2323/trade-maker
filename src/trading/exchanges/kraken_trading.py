import urllib.parse

import requests
import hashlib
import hmac
import time
import base64
import json
from src.logger import logger


class KrakenTrading:
    def __init__(self, api_key, api_secret, sandbox=True):
        """
        Initialize KrakenTrading instance.
        :param api_key: Kraken API key.
        :param api_secret: Kraken API secret.
        :param sandbox: Use sandbox environment if True.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://api.sandbox.kraken.com' if sandbox else 'https://api.kraken.com'


    def _sign(self, endpoint, data):
        """Generate Kraken API signature."""
        # Convert data to a URL-encoded string
        post_data = urllib.parse.urlencode(data).encode()
        message = f"/0/private/{endpoint}".encode() + hashlib.sha256(post_data).digest()
        secret = base64.b64decode(self.api_secret)
        signature = hmac.new(secret, message, hashlib.sha512).digest()
        return base64.b64encode(signature).decode()

    def _private_request(self, endpoint, data):
        """Make a private API request to Kraken."""
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._sign(endpoint, data),
        }
        url = f"{self.base_url}/0/private/{endpoint}"
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Kraken API request error: {e}")
            return None

    def get_balance(self):
        """Fetch account balance."""
        endpoint = 'Balance'
        return self._private_request(endpoint, {})

    def place_order(self, pair, side, volume, price=None):
        """
        Place an order.
        :param pair: Trading pair (e.g., 'XBTUSD').
        :param side: 'buy' or 'sell'.
        :param volume: Order size.
        :param price: Optional; specify for limit orders.
        """
        endpoint = 'AddOrder'
        order_data = {
            'pair': pair,
            'type': side,
            'ordertype': 'limit' if price else 'market',
            'volume': volume,
        }
        if price:
            order_data['price'] = price
        return self._private_request(endpoint, order_data)
