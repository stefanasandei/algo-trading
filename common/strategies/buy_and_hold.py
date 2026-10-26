from common.strategy import Strategy, Signal


class BuyAndHoldStrategy(Strategy):
    def run(self, symbol: str) -> Signal:
        return Signal.BUY
