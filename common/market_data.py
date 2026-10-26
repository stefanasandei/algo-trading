from dotenv import load_dotenv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
import os


from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed
from alpaca.common.enums import Sort

import pandas as pd
import yfinance as yf

from common.bar_cache import bar_path


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


class ParquetMarketData(MarketData):

    def __init__(self, directory: str, minutes: int):
        super().__init__()
        self.directory = directory
        self.minutes = minutes
        self.frames: dict[str, pd.DataFrame] = {}
        self.cursor: datetime | None = None

    def _frame(self, symbol: str) -> pd.DataFrame:
        if symbol not in self.frames:
            df = pd.read_parquet(bar_path(self.directory, symbol, self.minutes))
            self.frames[symbol] = df.sort_values("timestamp").reset_index(drop=True)
        return self.frames[symbol]

    def load(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        df = self._frame(symbol)
        return df[(df.timestamp >= start) & (df.timestamp < end)]

    def replay(self, symbol: str, start: datetime, end: datetime) -> list[datetime]:
        # Close time of each bar; a bar is complete once its close is reached.
        # A list (not a generator) so tqdm knows the total.
        return [ts + timedelta(minutes=self.minutes) for ts in self.load(symbol, start, end).timestamp]

    def set_cursor(self, t: datetime):
        self.cursor = t

    def get_candles(self, symbol: str, minutes: int, limit: int) -> list[Candle]:
        df = self._frame(symbol)
        # Only bars that closed at or before the cursor are visible.
        end = df.timestamp.searchsorted(self.cursor - timedelta(minutes=self.minutes), side="right")
        rows = df.iloc[max(0, end - limit):end][["timestamp", "open", "high", "low", "close", "volume"]]
        return [Candle(*r) for r in rows.itertuples(index=False)]
