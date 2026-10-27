import time

from common.market_data import AlpacaMarketView
from common.strategies.sma import SmaStrategy


def main():
    view = AlpacaMarketView(minutes=5)
    strategy = SmaStrategy(["AAPL"])

    last_bar = None

    while True:
        closes = view.closes(strategy.symbols, None, 1)
        if not closes.empty and closes.index[-1] != last_bar:
            t = closes.index[-1] + view.bar

            weight = strategy.targets(view, t)["AAPL"]
            decision = "LONG" if weight else "FLAT"

            print(f"{t:%d.%m.%Y %H:%M:%S}| AAPL: {decision}", flush=True)

            last_bar = closes.index[-1]
        time.sleep(view.bar.total_seconds())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
