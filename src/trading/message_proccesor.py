from src.logger import logger


class MessageProcessor:
    def __init__(self, trade_evaluator, trade_executor, position_manager, fee_calculator):
        """
        Initialize the MessageProcessor.
        :param trade_evaluator: Instance of TradeEvaluator.
        :param trade_executor: Instance of TradeExecutor.
        :param position_manager: Instance of PositionManager.
        :param fee_calculator: Instance of FeeCalculator.
        """
        self.trade_evaluator = trade_evaluator
        self.trade_executor = trade_executor
        self.position_manager = position_manager
        self.fee_calculator = fee_calculator

    def process_message(self, message):
        """
        Process a single message through the trading flow.
        :param message: The incoming message as a dictionary.
        """
        try:
            logger.debug(f"Processing message: {message}")

            # Step 1: Evaluate the trade opportunity
            evaluation_result = self.trade_evaluator.evaluate(message)
            if not evaluation_result:
                logger.debug("No trade opportunity found.")
                return

            logger.debug(f"Trade opportunity detected: {evaluation_result}")

            # Step 2: Extract trade details
            instrument_id = evaluation_result["instrument_id"]
            side = evaluation_result["trade_decision"].lower()  # 'buy' or 'sell'
            price = evaluation_result["price"]
            amount = 100 / price  # Example: Buy 100 USD worth of the asset

            # Step 3: Check if a position already exists
            if instrument_id in self.position_manager.positions:
                logger.debug(f"Position already exists for {instrument_id}. Skipping trade.")
                return

            # Step 4: Execute the trade
            order = self.trade_executor.execute_trade(instrument_id, side, amount, price)
            if not order:
                logger.error("Trade execution failed.")
                return

            logger.info(f"Trade executed successfully: {order}")

            # Step 5: Add the position
            self.position_manager.add_position(instrument_id, amount, price)

            # Step 6: Calculate fees
            fee = self.fee_calculator.calculate_fee(amount, price, order_type="limit" if price else "market")
            logger.info(f"Estimated fee for the trade: {fee}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
