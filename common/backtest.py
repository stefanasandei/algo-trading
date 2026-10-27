from dataclasses import dataclass
from datetime import datetime
from math import sqrt

import pandas as pd
from tqdm import tqdm

from common.market_data import MarketView
from common.strategy import Strategy


@dataclass
class BacktestReport:
    weights: pd.DataFrame
    returns: pd.Series
    equity: pd.Series
    profit: float
    sharpe: float


def backtest(
    strategy: Strategy,
    view: MarketView,
    start: datetime,
    end: datetime,
    bars_per_year: float | None = None,
) -> BacktestReport:
    prices = view.history(strategy.symbols, start, end)
    if len(prices) < 2:
        raise ValueError("Backtest needs at least two bars")

    targets = [strategy.targets(view, t) for t in tqdm(prices.index + view.bar)]
    weights = pd.DataFrame(targets, index=prices.index)
    weights = weights.reindex(columns=strategy.symbols).fillna(0.0)

    # Targets chosen at a bar's close apply to the following bar's return.
    asset_returns = prices.pct_change(fill_method=None)
    returns = (weights.shift(1) * asset_returns).sum(axis=1)
    equity = (1 + returns).cumprod()

    # The first bar has no previous position, so exclude it from Sharpe.
    realized = returns.iloc[1:]
    if bars_per_year is None:
        years = (prices.index[-1] - prices.index[0]) / pd.Timedelta(days=365.25)
        bars_per_year = len(realized) / years
    volatility = realized.std()
    sharpe = realized.mean() / volatility * sqrt(bars_per_year) if volatility > 0 else 0.0

    return BacktestReport(
        weights=weights,
        returns=returns,
        equity=equity,
        profit=equity.iloc[-1] - 1,
        sharpe=sharpe,
    )
