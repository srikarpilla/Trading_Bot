#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet (USDT-M) trading bot.

Examples
--------
    python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.01 --price 65000
    python cli.py --symbol BTCUSDT --side BUY  --type STOP   --quantity 0.01 --price 64000 --stop-price 64100

    # Validate input and preview the request without sending it to Binance:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
"""
import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceFuturesTestnetClient
from bot.exceptions import BinanceAPIError, NetworkError, TradingBotError, ValidationError
from bot.logging_config import setup_logging
from bot.orders import OrderManager, build_order_request


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Place MARKET / LIMIT / STOP orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument(
        "--side", required=True, type=str.upper, choices=["BUY", "SELL"], help="Order side"
    )
    parser.add_argument(
        "--type", dest="order_type", required=True, type=str.upper,
        choices=["MARKET", "LIMIT", "STOP"],
        help="Order type (STOP = stop-limit, bonus third type)",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", default=None, help="Limit price (required for LIMIT/STOP)")
    parser.add_argument(
        "--stop-price", dest="stop_price", default=None,
        help="Stop trigger price (required for STOP orders)",
    )
    parser.add_argument(
        "--time-in-force", dest="time_in_force", default="GTC",
        choices=["GTC", "IOC", "FOK"], help="Time in force for LIMIT/STOP orders (default: GTC)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate and print the order without sending it to Binance",
    )
    return parser.parse_args(argv)


def get_client() -> BinanceFuturesTestnetClient:
    load_dotenv()
    api_key = os.getenv("BINANCE_TESTNET_API_KEY")
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET")
    base_url = os.getenv("BINANCE_TESTNET_BASE_URL", "https://testnet.binancefuture.com")
    if not api_key or not api_secret:
        raise TradingBotError(
            "Missing API credentials. Set BINANCE_TESTNET_API_KEY and "
            "BINANCE_TESTNET_API_SECRET as environment variables or in a .env file "
            "(see .env.example)."
        )
    return BinanceFuturesTestnetClient(api_key, api_secret, base_url=base_url)


def main(argv=None) -> int:
    logger = setup_logging()
    args = parse_args(argv)

    # ---- validate input -------------------------------------------------
    try:
        order_request = build_order_request(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.time_in_force,
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        print(f"Invalid input: {exc}")
        return 2

    print(order_request.summary())

    if args.dry_run:
        print("\n[DRY RUN] Order was validated but NOT sent to Binance.")
        return 0

    # ---- build client -----------------------------------------------------
    try:
        client = get_client()
    except TradingBotError as exc:
        logger.error(str(exc))
        print(f"Configuration error: {exc}")
        return 2

    # ---- place order -------------------------------------------------------
    manager = OrderManager(client)
    try:
        response = manager.place(order_request)
    except ValidationError as exc:
        print(f"Invalid input: {exc}")
        return 2
    except BinanceAPIError as exc:
        print(f"Order failed (Binance API error): {exc}")
        return 1
    except NetworkError as exc:
        print(f"Order failed (network error): {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - last-resort safety net, fully logged
        logger.exception("Unexpected error while placing order")
        print(f"Order failed (unexpected error): {exc}")
        return 1

    print()
    print(OrderManager.format_response(response))
    print("\nSUCCESS: order placed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
