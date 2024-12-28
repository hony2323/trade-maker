from src.logger import logger


class FeeCalculator:
    def __init__(self, maker_fee=0.001, taker_fee=0.002):
        """
        Initialize the FeeCalculator.
        :param maker_fee: Fee for limit orders (as a fraction).
        :param taker_fee: Fee for market orders (as a fraction).
        """
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

    def calculate_fee(self, amount, price, order_type="market"):
        """
        Calculate the fee for a trade.
        :param amount: The amount traded.
        :param price: The price at which the trade occurred.
        :param order_type: 'market' or 'limit'.
        :return: The calculated fee.
        """
        fee_rate = self.taker_fee if order_type == "market" else self.maker_fee
        fee = amount * price * fee_rate
        logger.info(f"Calculated fee: {fee} ({order_type} order)")
        return fee
