import os
import time

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from common.market_data import AlpacaMarketView
from common.strategies.sma import SmaStrategy


def main():
    symbols = ["AAPL", "MSFT"]
    view = AlpacaMarketView(minutes=5)
    client = TradingClient(
        os.environ["ALPACA_KEY"], os.environ["ALPACA_SECRET"], paper=True
    )
    strategy = SmaStrategy(symbols)

    last_bar = None
    delay = 0
    print(f"Paper trading: {', '.join(symbols)}", flush=True)

    while True:
        time.sleep(delay)
        delay = view.bar.total_seconds()
        clock = client.get_clock()
        if not clock.is_open:
            print(f"Market closed. Next open: {clock.next_open}", flush=True)
            continue

        closes = view.closes(symbols, None, 1)
        if closes.empty:
            print("No common bars available.", flush=True)
            continue
        if closes.index[-1] == last_bar:
            print("Waiting for a new bar.", flush=True)
            continue

        t = closes.index[-1] + view.bar
        targets = strategy.targets(view, t)
        positions = {p.symbol for p in client.get_all_positions()}

        for symbol, weight in targets.items():
            decision = "LONG" if weight else "FLAT"
            print(f"{t:%d.%m.%Y %H:%M:%S}| {symbol}: {decision}", flush=True)

            orders = client.get_orders(
                filter=GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol])
            )
            if orders:
                print(f"{symbol}: order pending", flush=True)
                continue

            if not weight:
                if symbol in positions:
                    order = client.close_position(symbol)
                    print(f"{symbol}: close order {order.id}", flush=True)
                continue

            if symbol in positions:
                print(f"{symbol}: already invested", flush=True)
                continue

            account = client.get_account()
            amount = round(min(
                float(account.equity) * weight,
                float(account.cash),
                float(account.buying_power),
            ) * 0.99, 2)
            if amount < 1:
                print(f"{symbol}: insufficient cash", flush=True)
                continue

            order = client.submit_order(
                MarketOrderRequest(
                    symbol=symbol,
                    notional=amount,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
            )
            print(f"{symbol}: buy ${amount:.2f}, order {order.id}", flush=True)

        last_bar = closes.index[-1]


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
