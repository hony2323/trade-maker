import ccxt

from src.logger import logger


class TradeExecutor:
    def __init__(self, exchange_name, api_key, api_secret, demo_mode=True):
        """
        Initialize the TradeExecutor.
        :param exchange_name: Name of the exchange (e.g., 'binance').
        :param api_key: API key for the exchange.
        :param api_secret: API secret for the exchange.
        :param demo_mode: True for demo mode, False for live trading.
        """
        self.exchange = getattr(ccxt, exchange_name)({
            "apiKey": api_key,
            "secret": api_secret,
        })
        if demo_mode and hasattr(self.exchange, "set_sandbox_mode"):
            self.exchange.set_sandbox_mode(True)

    def execute_trade(self, instrument_id, side, amount, price=None):
        """
        Execute a trade on the exchange.
        :param instrument_id: The trading pair (e.g., 'BTC/USDT').
        :param side: 'buy' or 'sell'.
        :param amount: The amount to trade.
        :param price: The price for limit orders (None for market orders).
        :return: The response from the exchange API.
        """
        try:
            order_type = "limit" if price else "market"
            instrument_id = self.parse_symbol(instrument_id)
            order = self.exchange.create_order(instrument_id, order_type, side, amount, price)
            logger.info(f"Executed trade: {order}")
            return order
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}", exc_info=True)
            return None

    def parse_symbol(self, instrument_id):
        """
        Parse the symbol for the exchange.
        :param instrument_id: The trading pair (e.g., 'BTC-USD').
        :return: The symbol used by the exchange (e.g., 'BTC/USDT').
        """
        full_replace = True
        if "USDT" in instrument_id:
            full_replace = False
        if "USD" not in instrument_id:
            full_replace = False
        instrument_id = instrument_id.replace("-", "/")
        if full_replace:
            instrument_id = instrument_id.replace("USD", "USDT")
        return instrument_id
