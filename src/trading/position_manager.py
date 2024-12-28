from src.logger import logger


class PositionManager:
    def __init__(self):
        """
        Initialize the PositionManager to track open positions.
        """
        self.positions = {}  # Store positions as {instrument_id: position_data}

    def add_position(self, instrument_id, amount, price):
        """
        Add a new position.
        :param instrument_id: The trading pair (e.g., 'BTC/USDT').
        :param amount: The amount of the position.
        :param price: The entry price of the position.
        """
        self.positions[instrument_id] = {
            "amount": amount,
            "entry_price": price,
        }
        logger.info(f"Position added: {instrument_id}, amount: {amount}, price: {price}")

    def close_position(self, instrument_id):
        """
        Close a position and calculate P&L.
        :param instrument_id: The trading pair to close.
        :return: The closed position data.
        """
        position = self.positions.pop(instrument_id, None)
        if position:
            logger.info(f"Position closed: {instrument_id}, details: {position}")
        return position
