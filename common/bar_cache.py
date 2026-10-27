from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

import pandas as pd
from alpaca.common.enums import Sort
from alpaca.data.enums import DataFeed
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def bar_path(directory: str | Path, symbol: str, minutes: int) -> Path:
    return Path(directory) / f"{symbol}_{minutes}Min.parquet"


def sync_sip_bars(client, symbols: list[str], minutes: int, start: datetime, end: datetime, directory: str | Path):
    # Free plan: SIP history is only available older than 15 minutes.
    end = min(end, datetime.now(timezone.utc) - timedelta(minutes=16))
    if start >= end:
        return
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Work out the missing range per symbol, then group symbols by range
    # so each group is fetched with a single multi-symbol request.
    jobs: dict[tuple[datetime, datetime], list[str]] = {}
    for s in symbols:
        p = bar_path(directory, s, minutes)
        if not p.exists():
            jobs.setdefault((start, end), []).append(s)
            continue
        ts = pd.read_parquet(p, columns=["timestamp"])["timestamp"]
        if ts.empty:
            jobs.setdefault((start, end), []).append(s)
            continue
        if ts.min() > start:
            jobs.setdefault((start, min(ts.min(), end)), []).append(s)
        if ts.max() < end:
            jobs.setdefault((max(ts.max(), start), end), []).append(s)

    for (a, b), group in jobs.items():
        req = StockBarsRequest(
            symbol_or_symbols=group,
            timeframe=TimeFrame(minutes, TimeFrameUnit.Minute),
            start=a,
            end=b,
            feed=DataFeed.SIP,
            sort=Sort.ASC,
        )
        bars = client.get_stock_bars(req).df
        time.sleep(0.35)  # stay under 200 req/min
        if bars.empty:
            continue
        for s, new in bars.reset_index().groupby("symbol"):
            p = bar_path(directory, s, minutes)
            new = new[COLUMNS]
            if p.exists():
                new = pd.concat([pd.read_parquet(p), new])
            new.drop_duplicates("timestamp", keep="last").sort_values("timestamp").to_parquet(p, index=False)
