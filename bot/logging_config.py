import logging
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    """Configure basic file logging for the trading bot."""
    logging.basicConfig(
        filename=os.path.join(LOG_DIR, "trading.log"),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )