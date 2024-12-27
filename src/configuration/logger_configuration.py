import dataclasses
import os


@dataclasses.dataclass
class LoggerConfiguration:
    FILE_LOG_LEVEL = os.getenv("FILE_LOG_LEVEL", "INFO")
    CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", "INFO")
