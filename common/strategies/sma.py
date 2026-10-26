from datetime import datetime

from common.market_data import MarketView
from common.strategy import Strategy


class SmaStrategy(Strategy):

    def targets(self, view: MarketView, t: datetime | None) -> dict[str, float]:
        symbol = self.symbols[0]
        closes = view.closes([symbol], t, 20)[symbol]

        if len(closes) < 20:
            return {symbol: 0.0}

        sma = sum(closes) / len(closes)

        return {symbol: 1.0 if closes.iloc[-1] > sma else 0.0}
