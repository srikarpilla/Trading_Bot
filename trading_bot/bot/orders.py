"""Order construction, placement, and formatting.

This layer sits between the CLI and the raw API client: it turns
validated, human-friendly input into a Binance order payload, sends it
through the client, and formats the response for display. Keeping this
separate from cli.py means it can be unit tested (with a fake/mocked
client) without touching argparse or the network at all.
"""
import logging

from .client import BinanceFuturesTestnetClient
from .exceptions import BinanceAPIError, NetworkError
from .validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = logging.getLogger("trading_bot")


class OrderRequest:
    """A validated, ready-to-send order request."""

    def __init__(self, symbol, side, order_type, quantity, price=None,
                 stop_price=None, time_in_force="GTC"):
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force

    def to_binance_params(self) -> dict:
        params = {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.order_type,
            "quantity": str(self.quantity),
        }
        if self.order_type in ("LIMIT", "STOP"):
            params["price"] = str(self.price)
            params["timeInForce"] = self.time_in_force
        if self.order_type == "STOP":
            params["stopPrice"] = str(self.stop_price)
        return params

    def summary(self) -> str:
        lines = [
            "Order Request Summary",
            "----------------------",
            f"  Symbol      : {self.symbol}",
            f"  Side        : {self.side}",
            f"  Type        : {self.order_type}",
            f"  Quantity    : {self.quantity}",
        ]
        if self.price is not None:
            lines.append(f"  Price       : {self.price}")
        if self.stop_price is not None:
            lines.append(f"  Stop Price  : {self.stop_price}")
        if self.order_type in ("LIMIT", "STOP"):
            lines.append(f"  TimeInForce : {self.time_in_force}")
        return "\n".join(lines)


def build_order_request(symbol, side, order_type, quantity, price=None,
                         stop_price=None, time_in_force="GTC") -> OrderRequest:
    """Validate raw CLI input and return an OrderRequest (raises ValidationError)."""
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)
    stop_price = validate_stop_price(stop_price, order_type)
    return OrderRequest(symbol, side, order_type, quantity, price, stop_price, time_in_force)


class OrderManager:
    """High-level facade used by the CLI to place orders and report results."""

    def __init__(self, client: BinanceFuturesTestnetClient):
        self.client = client

    def place(self, order_request: OrderRequest) -> dict:
        logger.info(
            "Placing %s %s order for %s qty=%s",
            order_request.order_type, order_request.side,
            order_request.symbol, order_request.quantity,
        )
        params = order_request.to_binance_params()
        try:
            response = self.client.place_order(**params)
        except (BinanceAPIError, NetworkError):
            logger.exception("Order placement failed for %s", order_request.symbol)
            raise
        logger.info(
            "Order placed successfully: orderId=%s status=%s",
            response.get("orderId"), response.get("status"),
        )
        return response

    @staticmethod
    def format_response(response: dict) -> str:
        avg_price = response.get("avgPrice")
        lines = [
            "Order Response",
            "--------------",
            f"  Order ID     : {response.get('orderId')}",
            f"  Symbol       : {response.get('symbol')}",
            f"  Status       : {response.get('status')}",
            f"  Executed Qty : {response.get('executedQty')}",
        ]
        if avg_price not in (None, "0", "0.00", 0):
            lines.append(f"  Avg Price    : {avg_price}")
        return "\n".join(lines)
