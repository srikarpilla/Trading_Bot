from unittest.mock import MagicMock

import pytest

from bot.exceptions import BinanceAPIError, ValidationError
from bot.orders import OrderManager, build_order_request


def test_build_order_request_market():
    req = build_order_request(symbol="btcusdt", side="buy", order_type="market", quantity="0.01")
    params = req.to_binance_params()
    assert params == {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.01",
    }


def test_build_order_request_limit():
    req = build_order_request(
        symbol="ethusdt", side="sell", order_type="limit", quantity="1", price="3200.5"
    )
    params = req.to_binance_params()
    assert params["price"] == "3200.5"
    assert params["timeInForce"] == "GTC"


def test_build_order_request_stop_bonus():
    req = build_order_request(
        symbol="btcusdt", side="buy", order_type="stop", quantity="0.01",
        price="64000", stop_price="64100",
    )
    params = req.to_binance_params()
    assert params["stopPrice"] == "64100"
    assert params["price"] == "64000"


def test_build_order_request_missing_price_for_limit_raises():
    with pytest.raises(ValidationError):
        build_order_request(symbol="btcusdt", side="buy", order_type="limit", quantity="0.01")


def test_order_manager_place_success():
    fake_client = MagicMock()
    fake_client.place_order.return_value = {
        "orderId": 123456,
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "executedQty": "0.01",
        "avgPrice": "65000.10",
    }
    req = build_order_request(symbol="btcusdt", side="buy", order_type="market", quantity="0.01")
    manager = OrderManager(fake_client)
    response = manager.place(req)

    fake_client.place_order.assert_called_once_with(
        symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.01"
    )
    assert response["orderId"] == 123456
    formatted = OrderManager.format_response(response)
    assert "FILLED" in formatted
    assert "65000.10" in formatted


def test_order_manager_place_propagates_api_error():
    fake_client = MagicMock()
    fake_client.place_order.side_effect = BinanceAPIError("Insufficient margin", code=-2019)
    req = build_order_request(symbol="btcusdt", side="buy", order_type="market", quantity="0.01")
    manager = OrderManager(fake_client)

    with pytest.raises(BinanceAPIError):
        manager.place(req)
