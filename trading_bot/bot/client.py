"""Thin, signed REST client for Binance USDT-M Futures Testnet.

This is the ONLY module that knows how to talk HTTP to Binance. It has
no CLI code and no order-building logic in it - that separation is what
lets bot/orders.py and cli.py be tested independently of the network.

Every request and response is logged (safe_params strips the signature)
so that a full audit trail of what was sent/received ends up in
logs/trading_bot.log.
"""
import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

from .exceptions import BinanceAPIError, NetworkError

logger = logging.getLogger("trading_bot")

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_RECV_WINDOW = 5000


class BinanceFuturesTestnetClient:
    """Minimal signed REST client for Binance USDT-M Futures Testnet."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        recv_window: int = DEFAULT_RECV_WINDOW,
    ):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret are required.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.recv_window = recv_window
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ---------------------------------------------------------------- #
    # low-level helpers
    # ---------------------------------------------------------------- #
    def _sign(self, params: dict) -> str:
        query_string = urlencode(params, doseq=True)
        return hmac.new(
            self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, path: str, params: dict = None, signed: bool = True):
        params = dict(params or {})
        url = f"{self.base_url}{path}"

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self.recv_window
            params["signature"] = self._sign(params)

        safe_params = {k: v for k, v in params.items() if k != "signature"}
        logger.debug("REQUEST %s %s | params=%s", method, url, safe_params)

        try:
            response = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            logger.error("Network timeout calling %s %s: %s", method, url, exc)
            raise NetworkError(f"Request to {path} timed out after {self.timeout}s.") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error calling %s %s: %s", method, url, exc)
            raise NetworkError(
                f"Could not connect to {self.base_url}. Check your internet connection / DNS."
            ) from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Unexpected network error calling %s %s: %s", method, url, exc)
            raise NetworkError(f"Unexpected network error: {exc}") from exc

        logger.debug(
            "RESPONSE %s %s | status=%s body=%s",
            method, url, response.status_code, response.text[:2000],
        )

        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

        if response.status_code >= 400:
            code = data.get("code") if isinstance(data, dict) else None
            msg = data.get("msg") if isinstance(data, dict) else str(data)
            logger.error(
                "Binance API error %s (code=%s) on %s %s: %s",
                response.status_code, code, method, path, msg,
            )
            raise BinanceAPIError(
                f"Binance API error: {msg} (code={code})", code=code, status_code=response.status_code
            )

        return data

    # ---------------------------------------------------------------- #
    # public endpoints used by this bot
    # ---------------------------------------------------------------- #
    def get_server_time(self):
        return self._request("GET", "/fapi/v1/time", signed=False)

    def get_exchange_info(self):
        return self._request("GET", "/fapi/v1/exchangeInfo", signed=False)

    def get_account_balance(self):
        return self._request("GET", "/fapi/v2/balance", signed=True)

    def place_order(self, **order_params):
        """Submit a new order. order_params is a fully-formed Binance payload
        (symbol, side, type, quantity, price, timeInForce, stopPrice, ...)."""
        return self._request("POST", "/fapi/v1/order", params=order_params, signed=True)

    def get_order(self, symbol: str, order_id: int):
        return self._request(
            "GET", "/fapi/v1/order", params={"symbol": symbol, "orderId": order_id}, signed=True
        )

    def cancel_order(self, symbol: str, order_id: int):
        return self._request(
            "DELETE", "/fapi/v1/order", params={"symbol": symbol, "orderId": order_id}, signed=True
        )
