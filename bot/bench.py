from datetime import datetime, timezone

from common.backtest import backtest
from common.market_data import AlpacaMarketView, ParquetMarketView
from common.strategies.buy_and_hold import BuyAndHoldStrategy
from common.strategies.sma import SmaStrategy

print(SmaStrategy(["AAPL"]).targets(AlpacaMarketView(minutes=5)))

start = datetime(2023, 1, 1, tzinfo=timezone.utc)
end = datetime(2023, 12, 1, tzinfo=timezone.utc)
view = ParquetMarketView("./data", minutes=5)

sma = backtest(SmaStrategy(["AAPL"]), view, start, end)
baseline = backtest(BuyAndHoldStrategy(["SPY"]), view, start, end)

print(f"SMA AAPL: profit {sma.profit:.2%}, sharpe {sma.sharpe:.2f}")
print(f"Buy & hold SPY: profit {baseline.profit:.2%}")
