from dataclasses import dataclass
from datetime import datetime

import numpy as np
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
    close_times = prices.index + view.bar

    # Decide at each bar's close; hold the weights until the next bar's close.
    weights = []
    for t in tqdm(close_times):
        w = strategy.targets(view, t)
        weights.append([w.get(s, 0.0) for s in strategy.symbols])
    weights = pd.DataFrame(weights, index=prices.index, columns=strategy.symbols)

    asset_returns = prices.pct_change().shift(-1).fillna(0)
    returns = (weights * asset_returns).sum(axis=1)
    equity = (1 + returns).cumprod()

    years = (prices.index[-1] - prices.index[0]).total_seconds() / (365.25 * 86400)
    bars_per_year = bars_per_year or len(returns) / years
    sharpe = returns.mean() / returns.std() * np.sqrt(bars_per_year) if returns.std() else 0.0

    return BacktestReport(weights, returns, equity, equity.iloc[-1] - 1, sharpe)
