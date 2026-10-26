from dotenv import load_dotenv
import os

from alpaca.trading.client import TradingClient

load_dotenv()

trading_client = TradingClient(os.environ["ALPACA_KEY"], os.environ["ALPACA_SECRET"])

print(trading_client.get_account().buying_power)
