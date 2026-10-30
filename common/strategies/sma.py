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
        targets = {}
        for symbol in self.symbols:
            closes = view.closes([symbol], t, self.window)[symbol]
            targets[symbol] = 0.0

            if len(closes) < self.window:
                continue

            sma = sum(closes) / len(closes)
            if not closes.iloc[-1] > sma:
                continue

            targets[symbol] = 1.0 / len(self.symbols)

        return targets
