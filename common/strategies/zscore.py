from datetime import datetime
from math import isfinite

from common.market_data import MarketView
from common.strategy import Strategy


class ZScoreStrategy(Strategy):
    """Buy below -entry standard deviations; exit at the rolling mean."""

    def __init__(self, symbols: list[str], window: int = 20, entry: float = 2.0):
        super().__init__(symbols)
        if len(symbols) != 1 or window < 2 or not isfinite(entry) or entry <= 0:
            raise ValueError("Bad parameters")
        self.window = window
        self.entry = entry
        self.weight = 0.0

    def targets(self, view: MarketView, t: datetime | None = None) -> dict[str, float]:
        symbol = self.symbols[0]
        closes = view.closes([symbol], t, self.window)[symbol]
        std = closes.std(ddof=0)

        if len(closes) < self.window or not isfinite(std) or std == 0:
            self.weight = 0.0
        else:
            z = (closes.iloc[-1] - closes.mean()) / std
            if z <= -self.entry:
                self.weight = 1.0
            elif z >= 0:
                self.weight = 0.0

        return {symbol: self.weight}
