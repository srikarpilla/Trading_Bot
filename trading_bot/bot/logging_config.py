"""Centralized logging configuration.

- A rotating file handler writes DEBUG-level detail (every API request,
  every response, every error) to logs/trading_bot.log.
- A console handler writes concise INFO-level messages so the terminal
  output stays readable while the file keeps the full trail.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PACKAGE_DIR)
LOG_DIR = os.path.join(_PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

_LOGGER_NAME = "trading_bot"


def setup_logging(log_level=logging.DEBUG, console_level=logging.INFO, log_file=None):
    """Idempotently configure and return the shared 'trading_bot' logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = log_file or LOG_FILE

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        # Already configured (e.g. tests calling this more than once).
        return logger

    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
