from datetime import datetime

from common.market_data import MarketView
from common.strategy import Strategy


class SmaStrategy(Strategy):

    def __init__(self, symbols: list[str], window: int = 20):
        super().__init__(symbols)
        if window < 1:
            raise ValueError("SMA window must be positive")
        self.window = window

    def targets(self, view: MarketView, t: datetime | None = None) -> dict[str, float]:
        symbol = self.symbols[0]
        closes = view.closes([symbol], t, self.window)[symbol]

        if len(closes) < self.window:
            return {symbol: 0.0}

        sma = sum(closes) / len(closes)

        return {symbol: 1.0 if closes.iloc[-1] > sma else 0.0}
