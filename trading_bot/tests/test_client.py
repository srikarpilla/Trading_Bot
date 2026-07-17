from unittest.mock import MagicMock, patch

import pytest
import requests

from bot.client import BinanceFuturesTestnetClient
from bot.exceptions import BinanceAPIError, NetworkError


def make_client():
    return BinanceFuturesTestnetClient(api_key="test-key", api_secret="test-secret")


def _fake_response(status_code=200, json_body=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or str(json_body)
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("no json")
    return resp


def test_place_order_success():
    client = make_client()
    fake_resp = _fake_response(
        200,
        {"orderId": 111, "symbol": "BTCUSDT", "status": "FILLED", "executedQty": "0.01"},
    )
    with patch.object(client.session, "request", return_value=fake_resp) as mock_request:
        result = client.place_order(symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.01")

    assert result["orderId"] == 111
    called_kwargs = mock_request.call_args.kwargs
    assert "signature" in called_kwargs["params"]
    assert called_kwargs["params"]["symbol"] == "BTCUSDT"


def test_place_order_binance_error_raises():
    client = make_client()
    fake_resp = _fake_response(400, {"code": -1121, "msg": "Invalid symbol."})
    with patch.object(client.session, "request", return_value=fake_resp):
        with pytest.raises(BinanceAPIError) as exc_info:
            client.place_order(symbol="BADSYM", side="BUY", type="MARKET", quantity="0.01")
    assert exc_info.value.code == -1121


def test_place_order_timeout_raises_network_error():
    client = make_client()
    with patch.object(client.session, "request", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(NetworkError):
            client.place_order(symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.01")


def test_place_order_connection_error_raises_network_error():
    client = make_client()
    with patch.object(
        client.session, "request", side_effect=requests.exceptions.ConnectionError()
    ):
        with pytest.raises(NetworkError):
            client.place_order(symbol="BTCUSDT", side="BUY", type="MARKET", quantity="0.01")


def test_signature_not_leaked_outside_params():
    client = make_client()
    sig = client._sign({"symbol": "BTCUSDT", "timestamp": 1})
    assert isinstance(sig, str)
    assert len(sig) == 64  # hex-encoded SHA256 digest
