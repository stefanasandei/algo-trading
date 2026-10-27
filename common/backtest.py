from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from math import sqrt

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
    progress: bool = True,
) -> BacktestReport:
    prices = view.history(strategy.symbols, start, end)
    if len(prices) < 2:
        raise ValueError("Backtest needs at least two bars")

    targets = [
        strategy.targets(view, t)
        for t in tqdm(prices.index + view.bar, desc="Backtest", disable=not progress)
    ]
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


def walk_forward(
    strategies: list[Strategy],
    view: MarketView,
    start: datetime,
    end: datetime,
    train_bars: int,
    test_bars: int,
    bars_per_year: float | None = None,
    progress: bool = True,
) -> BacktestReport:
    """Select by training Sharpe on a sliding window; return only test results.

    Windows advance by test_bars, including a shorter final test window.
    Each backtest uses a fresh copy of the candidate strategy.
    """
    if not strategies or train_bars < 2 or test_bars < 1:
        raise ValueError("Need strategies, at least two training bars and one test bar")

    symbols = list(dict.fromkeys(s for strategy in strategies for s in strategy.symbols))
    prices = view.history(symbols, start, end)
    if len(prices) <= train_bars:
        raise ValueError("Walk-forward needs training bars and at least one test bar")

    reports = []
    windows = range(train_bars, len(prices), test_bars)
    for i in tqdm(windows, desc="Walk-forward", disable=not progress):
        train_start = prices.index[i - train_bars]
        test_start = prices.index[i - 1] + view.bar
        scores = [
            backtest(deepcopy(s), view, train_start, test_start, bars_per_year, progress=False).sharpe
            for s in strategies
        ]
        best = strategies[max(range(len(scores)), key=scores.__getitem__)]
        test_end = prices.index[min(i + test_bars, len(prices)) - 1] + view.bar
        report = backtest(
            deepcopy(best), view, prices.index[i - 1], test_end, bars_per_year, progress=False
        )
        reports.append(report)

    returns = pd.concat([r.returns.iloc[1:] for r in reports])
    weights = pd.concat([r.weights for r in reports]).fillna(0.0)
    weights = weights.loc[~weights.index.duplicated(keep="last")].reindex(returns.index)
    equity = (1 + returns).cumprod()
    if bars_per_year is None:
        years = (returns.index[-1] - prices.index[train_bars - 1]) / pd.Timedelta(days=365.25)
        bars_per_year = len(returns) / years
    volatility = returns.std()
    sharpe = returns.mean() / volatility * sqrt(bars_per_year) if volatility > 0 else 0.0

    return BacktestReport(weights, returns, equity, equity.iloc[-1] - 1, sharpe)


def monte_carlo(
    returns: pd.Series,
    simulations: int = 1000,
    seed: int | None = None,
    progress: bool = True,
) -> pd.DataFrame:
    """Bootstrap independent returns; report profit and positive max drawdown per path."""
    values = returns.to_numpy(dtype=float)
    if simulations < 1 or not len(values):
        raise ValueError("Need returns and at least one simulation")
    if not np.isfinite(values).all() or (values < -1).any():
        raise ValueError("Returns must be finite and at least -1")

    rng = np.random.default_rng(seed)
    results = []
    for _ in tqdm(range(simulations), desc="Monte Carlo", disable=not progress):
        sample = rng.choice(values, size=len(values), replace=True)
        equity = np.concatenate(([1.0], (1 + sample).cumprod()))
        drawdown = 1 - equity / np.maximum.accumulate(equity)
        results.append((equity[-1] - 1, drawdown.max()))

    return pd.DataFrame(results, columns=["profit", "max_drawdown"])
