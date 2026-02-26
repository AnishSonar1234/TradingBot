import os
import time
import logging
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    BASE_URL = "https://testnet.binancefuture.com/fapi"

    def __init__(self):
        """Wrap python-binance Client for Testnet USDT-margined futures."""
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("API credentials not found in environment variables")

        self.client = Client(api_key, api_secret)
        self.client.FUTURES_URL = self.BASE_URL

        # Sync timestamp with Binance Futures server time to avoid -1021 recvWindow errors
        res = self.client.futures_time()
        self.client.timestamp_offset = res["serverTime"] - int(time.time() * 1000)
        logger.debug(f"Timestamp offset: {self.client.timestamp_offset}ms")

    def create_order(self, **kwargs):
        """Send a signed futures order to Binance and log the full response."""
        try:
            logger.info(f"Sending order request: {kwargs}")
            response = self.client.futures_create_order(**kwargs)
            logger.info(f"Order response: {response}")
            return response
        except Exception:
            logger.exception("API Error while creating order")
            raise

    def get_mark_price(self, symbol: str) -> float:
        """Fetch the current mark price for a given futures symbol."""
        data = self.client.futures_mark_price(symbol=symbol)
        return float(data["markPrice"])

    def get_symbol_filters(self, symbol: str):
        """Return exchange trading filters (tick size, min notional, etc.) for a symbol."""
        info = self.client.futures_exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                return s["filters"]
        raise ValueError(f"Symbol {symbol} not found")