"""Input validation for order requests.

These are pure functions with no network dependency, so they run
instantly and are trivial to unit test. Symbol validation is a
lightweight format check; callers who want to guarantee a symbol is
actually tradable can additionally cross-check it against
client.get_exchange_info().
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from .exceptions import ValidationError

VALID_SIDES = {"BUY", "SELL"}
# STOP == stop-limit on Binance USDT-M futures (bonus third order type)
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}
SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,20}$")


def validate_symbol(symbol: str) -> str:
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol is required (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not SYMBOL_RE.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected an uppercase alphanumeric "
            f"symbol such as BTCUSDT or ETHUSDT."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValidationError("Side is required (BUY or SELL).")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValidationError("Order type is required (MARKET, LIMIT, or STOP).")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> Decimal:
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValidationError("Quantity must be greater than 0.")
    return qty


def validate_price(price, order_type: str) -> Optional[Decimal]:
    if order_type == "MARKET":
        if price is not None:
            raise ValidationError("Price must not be supplied for MARKET orders.")
        return None
    # LIMIT or STOP both need a limit price
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")
    try:
        price_dec = Decimal(str(price))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"Price '{price}' is not a valid number.")
    if price_dec <= 0:
        raise ValidationError("Price must be greater than 0.")
    return price_dec


def validate_stop_price(stop_price, order_type: str) -> Optional[Decimal]:
    if order_type != "STOP":
        if stop_price is not None:
            raise ValidationError("stop_price must only be supplied for STOP orders.")
        return None
    if stop_price is None:
        raise ValidationError("stop_price is required for STOP (stop-limit) orders.")
    try:
        sp = Decimal(str(stop_price))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"stop_price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValidationError("stop_price must be greater than 0.")
    return sp
