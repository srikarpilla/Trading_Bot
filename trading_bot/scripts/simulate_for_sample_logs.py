"""
Generates sample_logs/sample_trading_bot.log by running the REAL cli.py /
bot package code path (validation -> client -> logging) for one MARKET
and one LIMIT order.

IMPORTANT: This sandbox environment has no outbound network access to
Binance's servers, so this script monkeypatches
`requests.Session.request` to return realistic canned Binance Futures
Testnet responses instead of making a live call. Every other line of
code (signing, logging, formatting, error handling) is the genuine,
unmodified project code - only the actual HTTP transport is stubbed.

Candidates/reviewers running this project with real API keys against
the real https://testnet.binancefuture.com endpoint will get logs in
exactly this format in logs/trading_bot.log.
"""
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["BINANCE_TESTNET_API_KEY"] = "sample-testnet-api-key"
os.environ["BINANCE_TESTNET_API_SECRET"] = "sample-testnet-api-secret"

from bot.logging_config import LOG_FILE  # noqa: E402
import cli  # noqa: E402


def fake_response(status_code, json_body):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = str(json_body)
    resp.json.return_value = json_body
    return resp


MARKET_RESPONSE = fake_response(200, {
    "orderId": 5028953,
    "symbol": "BTCUSDT",
    "status": "FILLED",
    "clientOrderId": "sample1",
    "side": "BUY",
    "type": "MARKET",
    "origQty": "0.010",
    "executedQty": "0.010",
    "avgPrice": "65123.40",
    "cumQuote": "651.2340",
})

LIMIT_RESPONSE = fake_response(200, {
    "orderId": 5028961,
    "symbol": "ETHUSDT",
    "status": "NEW",
    "clientOrderId": "sample2",
    "side": "SELL",
    "type": "LIMIT",
    "origQty": "1.000",
    "executedQty": "0.000",
    "price": "3200.50",
    "timeInForce": "GTC",
})


def run(args, fake_resp):
    with patch("requests.Session.request", return_value=fake_resp):
        exit_code = cli.main(args)
    print(f"(exit code: {exit_code})\n")


if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    print("=== Simulated MARKET order ===")
    run(["--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--quantity", "0.01"],
        MARKET_RESPONSE)

    print("=== Simulated LIMIT order ===")
    run(["--symbol", "ETHUSDT", "--side", "SELL", "--type", "LIMIT",
         "--quantity", "1", "--price", "3200.50"], LIMIT_RESPONSE)

    print(f"Log written to: {LOG_FILE}")
