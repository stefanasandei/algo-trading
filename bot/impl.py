from common.market_data import AlpacaMarketData
from common.strategies.sma import SmaStrategy

alpaca_data = AlpacaMarketData()
sma_strategy = SmaStrategy(alpaca_data)

result = sma_strategy.run(symbol="AAPL")
print(result)
