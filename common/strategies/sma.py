from common.strategy import Strategy, Signal


class SmaStrategy(Strategy):
    def run(self, symbol: str) -> Signal:
        candles = self.data.get_candles(symbol, minutes=5, limit=20)

        if len(candles) < 20:
            return Signal.HOLD

        sma = sum(c.close for c in candles) / len(candles)

        return Signal.BUY if candles[-1].close > sma else Signal.SELL
