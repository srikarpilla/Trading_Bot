from decimal import Decimal

import pytest

from bot.exceptions import ValidationError
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def test_validate_symbol_ok():
    assert validate_symbol("btcusdt") == "BTCUSDT"


def test_validate_symbol_rejects_bad_chars():
    with pytest.raises(ValidationError):
        validate_symbol("BTC-USDT!")


def test_validate_symbol_rejects_empty():
    with pytest.raises(ValidationError):
        validate_symbol("")


def test_validate_side_ok():
    assert validate_side("buy") == "BUY"
    assert validate_side("SELL") == "SELL"


def test_validate_side_rejects_invalid():
    with pytest.raises(ValidationError):
        validate_side("HOLD")


def test_validate_order_type_ok():
    assert validate_order_type("market") == "MARKET"
    assert validate_order_type("stop") == "STOP"


def test_validate_order_type_rejects_invalid():
    with pytest.raises(ValidationError):
        validate_order_type("ICEBERG")


def test_validate_quantity_ok():
    assert validate_quantity("0.01") == Decimal("0.01")


def test_validate_quantity_rejects_zero_or_negative():
    with pytest.raises(ValidationError):
        validate_quantity("0")
    with pytest.raises(ValidationError):
        validate_quantity("-1")


def test_validate_quantity_rejects_non_numeric():
    with pytest.raises(ValidationError):
        validate_quantity("abc")


def test_validate_price_market_must_be_none():
    assert validate_price(None, "MARKET") is None
    with pytest.raises(ValidationError):
        validate_price("100", "MARKET")


def test_validate_price_limit_required():
    with pytest.raises(ValidationError):
        validate_price(None, "LIMIT")
    assert validate_price("65000", "LIMIT") == Decimal("65000")


def test_validate_price_rejects_non_positive():
    with pytest.raises(ValidationError):
        validate_price("0", "LIMIT")


def test_validate_stop_price_required_for_stop():
    with pytest.raises(ValidationError):
        validate_stop_price(None, "STOP")
    assert validate_stop_price("64100", "STOP") == Decimal("64100")


def test_validate_stop_price_forbidden_elsewhere():
    with pytest.raises(ValidationError):
        validate_stop_price("64100", "LIMIT")
