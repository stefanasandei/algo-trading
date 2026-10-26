from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import numpy as np
from tqdm import tqdm

from common.market_data import ParquetMarketData
from common.strategy import Signal, Strategy


@dataclass
class BacktestReport:
    signals: list[tuple[datetime, Signal]]
    profit: float
    sharpe: float


def backtest(
    strategy_factory: Callable[[ParquetMarketData], Strategy],
    source: ParquetMarketData,
    symbol: str,
    start: datetime,
    end: datetime,
    bars_per_year: float | None = None,
) -> BacktestReport:
    strategy = strategy_factory(source)
    close = source.load(symbol, start, end).close.to_numpy()
    times = source.replay(symbol, start, end)

    signals = []
    returns = []
    equity = 1.0
    position = 0  # 1 = long, 0 = flat

    for i, t in enumerate(tqdm(times)):
        source.set_cursor(t)
        signal = strategy.run(symbol)
        signals.append((t, signal))

        if signal == Signal.BUY:
            position = 1
        elif signal == Signal.SELL:
            position = 0  # HOLD keeps the current position

        # Earn the return from this bar's close to the next bar's close.
        r = 0.0
        if i + 1 < len(close):
            r = position * (close[i + 1] / close[i] - 1)
        returns.append(r)
        equity *= 1 + r

    returns = np.array(returns)
    years = (times[-1] - times[0]).total_seconds() / (365.25 * 86400)
    bars_per_year = bars_per_year or len(returns) / years
    sharpe = returns.mean() / returns.std() * np.sqrt(bars_per_year) if returns.std() else 0.0
    return BacktestReport(signals, equity - 1, sharpe)
