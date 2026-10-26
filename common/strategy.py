from abc import ABC, abstractmethod
from datetime import datetime

from common.market_data import MarketView


class Strategy(ABC):

    def __init__(self, symbols: list[str]):
        self.symbols = symbols

    @abstractmethod
    def targets(self, view: MarketView, t: datetime | None) -> dict[str, float]:
        """Target weight per symbol at t, e.g. {"AAPL": 1.0} or {"SPY": -1, "QQQ": 1}."""
