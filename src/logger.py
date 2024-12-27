import logging
from logging.handlers import TimedRotatingFileHandler
from src.configuration import LoggerConfiguration
import os

# Create the logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create a logger
logger = logging.getLogger("trade-maker-logger")
logger.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LoggerConfiguration.CONSOLE_LOG_LEVEL)  # Console logs INFO and above

# Create a file handler with rolling logs
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, "project.log"),
    when="midnight",  # Rotate logs at midnight
    interval=1,       # Every 1 day
    backupCount=7,    # Keep the last 7 logs
    encoding="utf-8"
)
file_handler.setLevel(LoggerConfiguration.FILE_LOG_LEVEL)  # File logs DEBUG and above

# Create a formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s - [%(module)s %(funcName)s %(lineno)d]"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Example logging
logger.info("Logger initialized successfully")
