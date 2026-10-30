# algo trading bot

A simple experiment bench to learn algo trading.

## setup

```sh
pip install -e .
```

Copy `.env.example` to `.env` and set `ALPACA_KEY` and `ALPACA_SECRET` to your Alpaca paper account credentials.

```sh
python3 ./bot/entry.py
```

Set `symbols` in `bot/entry.py` to choose stocks. Trades with `paper=True`: LONG buys an equal share of account equity with a 1% buffer, capped by cash and buying power; FLAT closes the position. Skips pending orders and closed markets.
