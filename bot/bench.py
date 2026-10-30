from datetime import datetime, timezone

from common.backtest import backtest, monte_carlo, walk_forward
from common.market_data import ParquetMarketView
from common.strategies.buy_and_hold import BuyAndHoldStrategy
from common.strategies.sma import SmaStrategy

start = datetime(2023, 1, 1, tzinfo=timezone.utc)
end = datetime(2023, 12, 1, tzinfo=timezone.utc)
view = ParquetMarketView("./data", minutes=5)

sma = backtest(SmaStrategy(["AAPL"]), view, start, end)
baseline = backtest(BuyAndHoldStrategy(["SPY"]), view, start, end)
forward = walk_forward(
    [SmaStrategy(["AAPL"], window=n) for n in [10, 20, 50]],
    view,
    start,
    end,
    train_bars=1000,
    test_bars=200,
)
simulations = monte_carlo(forward.returns, simulations=1000, seed=42)

print(f"SMA AAPL: profit {sma.profit:.2%}, sharpe {sma.sharpe:.2f}")
print(f"Buy & hold SPY: profit {baseline.profit:.2%}")
print(f"Walk-forward AAPL: profit {forward.profit:.2%}, sharpe {forward.sharpe:.2f}")
print("Monte Carlo percentiles:")
print(simulations.quantile([0.05, 0.5, 0.95]).to_string(float_format="{:.2%}".format))
