import json

from src.logger import logger


class TradeEvaluator:
    def __init__(self, threshold=0.01):
        """
        Initialize the TradeEvaluator.
        :param threshold: Minimum spread or condition to trigger a trade (e.g., 1% spread).
        """
        self.threshold = threshold

    def evaluate(self, message):
        """
        Evaluate the incoming message to determine if a trade opportunity exists.
        :param message: The parsed message as a dictionary.
        :return: A dictionary with evaluation results or None if no trade opportunity exists.
        """
        try:
            data = json.loads(message)
            price = data.get("price")
            best_bid = data.get("best_bid")
            best_ask = data.get("best_ask")

            # Example: Check if spread is above the threshold
            if best_ask - best_bid > self.threshold * price:
                return {
                    "trade_decision": "BUY",
                    "instrument_id": data["instrument_id"],
                    "price": price,
                    "timestamp": data["timestamp"],
                }
            return None
        except Exception as e:
            logger.error(f"Error evaluating trade opportunity: {e}", exc_info=True)
            return None
