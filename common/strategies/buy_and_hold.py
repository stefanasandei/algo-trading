from datetime import datetime

from common.market_data import MarketView
from common.strategy import Strategy


class BuyAndHoldStrategy(Strategy):

    def targets(self, view: MarketView, t: datetime | None) -> dict[str, float]:
        return {s: 1.0 for s in self.symbols}
