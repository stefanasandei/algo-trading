from datetime import datetime, timezone

from common.backtest import backtest
from common.market_data import AlpacaMarketData, ParquetMarketData
from common.strategies.buy_and_hold import BuyAndHoldStrategy
from common.strategies.sma import SmaStrategy

print(SmaStrategy(AlpacaMarketData()).run(symbol="AAPL"))

start = datetime(2023, 1, 1, tzinfo=timezone.utc)
end = datetime(2023, 12, 1, tzinfo=timezone.utc)
market_data = ParquetMarketData("./data", minutes=5)

sma = backtest(SmaStrategy, market_data, "AAPL", start, end)
baseline = backtest(BuyAndHoldStrategy, market_data, "SPY", start, end)

print(f"SMA AAPL: profit {sma.profit:.2%}, sharpe {sma.sharpe:.2f}")
print(f"Buy & hold SPY: profit {baseline.profit:.2%}")
