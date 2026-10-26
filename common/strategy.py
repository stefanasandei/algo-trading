from abc import ABC, abstractmethod
from enum import Enum

from common.market_data import AlpacaMarketData


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):

    def __init__(self, data: AlpacaMarketData):
        self.data = data

    @abstractmethod
    def run(self, symbol: str) -> Signal:
        pass
