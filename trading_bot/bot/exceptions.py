"""Custom exception hierarchy for the trading bot.

Keeping these distinct (instead of raising bare Exception / ValueError
everywhere) lets the CLI layer catch each failure mode separately and
print a clear, specific message instead of a stack trace.
"""


class TradingBotError(Exception):
    """Base class for all trading-bot-specific errors."""


class ValidationError(TradingBotError):
    """Raised when user/CLI input fails validation (bad symbol, side, etc.)."""


class NetworkError(TradingBotError):
    """Raised on connection failures, timeouts, or other transport-level errors."""


class BinanceAPIError(TradingBotError):
    """Raised when Binance responds with an error (HTTP >= 400 or an error body)."""

    def __init__(self, message, code=None, status_code=None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
