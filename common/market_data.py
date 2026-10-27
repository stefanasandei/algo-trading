from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import os

from alpaca.common.enums import Sort
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from dotenv import load_dotenv
import pandas as pd

from common.bar_cache import bar_path


class MarketView(ABC):
    """Bar closes as of a point in time. A bar is visible once its close <= t."""

    def __init__(self, minutes: int):
        self.minutes = minutes
        self.bar = timedelta(minutes=minutes)

    @abstractmethod
    def closes(self, symbols: list[str], t: datetime | None, n: int) -> pd.DataFrame:
        """Last n closes per symbol visible at t (None = latest). Columns = symbols."""

    @abstractmethod
    def history(self, symbols: list[str], start: datetime, end: datetime) -> pd.DataFrame:
        """Closes of bars starting in [start, end). Columns = symbols."""


class AlpacaMarketView(MarketView):

    def __init__(self, minutes: int, feed: DataFeed = DataFeed.IEX):
        super().__init__(minutes)
        load_dotenv()
        self.feed = feed
        self.client = StockHistoricalDataClient(
            os.environ["ALPACA_KEY"], os.environ["ALPACA_SECRET"]
        )

    def _series(self, symbol: str, **kwargs) -> pd.Series:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame(self.minutes, TimeFrameUnit.Minute),
            feed=self.feed,
            **kwargs,
        )
        bars = self.client.get_stock_bars(request).data.get(symbol, [])
        return pd.Series({b.timestamp: b.close for b in bars}, dtype=float).sort_index()

    def closes(self, symbols: list[str], t: datetime | None, n: int) -> pd.DataFrame:
        end = (t or datetime.now(timezone.utc)) - self.bar
        start = datetime(1970, 1, 1, tzinfo=timezone.utc)
        return pd.concat(
            {s: self._series(s, start=start, end=end, limit=n, sort=Sort.DESC) for s in symbols},
            axis=1,
            join="inner",
        )

    def history(self, symbols: list[str], start: datetime, end: datetime) -> pd.DataFrame:
        return pd.concat(
            {s: self._series(s, start=start, end=end - timedelta(microseconds=1), sort=Sort.ASC) for s in symbols},
            axis=1,
            join="inner",
        )


class ParquetMarketView(MarketView):

    def __init__(self, directory: str, minutes: int):
        super().__init__(minutes)
        self.directory = directory
        self.cache: dict[str, pd.Series] = {}

    def _load(self, symbol: str) -> pd.Series:
        if symbol not in self.cache:
            df = pd.read_parquet(bar_path(self.directory, symbol, self.minutes))
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            self.cache[symbol] = df.set_index("timestamp")["close"].sort_index()
        return self.cache[symbol]

    def closes(self, symbols: list[str], t: datetime | None, n: int) -> pd.DataFrame:
        # Index is bar start; a bar with start <= t - bar has closed by t.
        if len(symbols) == 1:
            c = self._load(symbols[0])
            end = len(c) if t is None else c.index.searchsorted(t - self.bar, side="right")
            return c.iloc[:end].tail(n).to_frame(name=symbols[0])

        series = {}
        for s in symbols:
            c = self._load(s)
            if t is not None:
                c = c.loc[: t - self.bar]
            series[s] = c.tail(n)
        return pd.concat(series, axis=1, join="inner")

    def history(self, symbols: list[str], start: datetime, end: datetime) -> pd.DataFrame:
        series = {}
        for s in symbols:
            c = self._load(s)
            series[s] = c.loc[(c.index >= start) & (c.index < end)]
        return pd.concat(series, axis=1, join="inner")
