# Sample Logs

`sample_trading_bot.log` in this folder was produced by running the
**real, unmodified** application code path (`cli.py` -> `bot/orders.py`
-> `bot/client.py` -> `bot/logging_config.py`) for one MARKET order and
one LIMIT order.

The only thing stubbed is the actual HTTP call
(`requests.Session.request`), because this sample was generated in a
sandboxed environment with no outbound network access to
`testnet.binancefuture.com`. Signing, request building, response
parsing, and logging are all the genuine project code - see
`scripts/simulate_for_sample_logs.py` for exactly what was stubbed.

When you run the bot yourself with real Binance Futures Testnet API
keys (see the main README), `logs/trading_bot.log` will be populated in
this exact format from live testnet responses - that is the file you
should submit as your deliverable log evidence.
