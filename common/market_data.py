from dotenv import load_dotenv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import os


from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed
from alpaca.common.enums import Sort

import yfinance as yf


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketData(ABC):

    def __init__(self):
        load_dotenv()

    @abstractmethod
    def get_candles(self, symbol: str, minutes: int, limit: int) -> list[Candle]:
        pass


class AlpacaMarketData(MarketData):

    def __init__(self):
        super().__init__()

        self.client = StockHistoricalDataClient(
            os.environ["ALPACA_KEY"], os.environ["ALPACA_SECRET"]
        )

    def get_candles(self, symbol: str, minutes: int, limit: int) -> list[Candle]:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(minutes, TimeFrameUnit.Minute),
            limit=limit,
            sort=Sort.DESC,
            feed=DataFeed.IEX,
        )

        bars = self.client.get_stock_bars(request)
        data = bars.data[symbol]

        return [
            Candle(
                timestamp=b.timestamp,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
            )
            for b in reversed(data)
        ]
