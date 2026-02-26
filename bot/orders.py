import logging
from decimal import Decimal, ROUND_DOWN

from bot.validators import (
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, client):
        """High-level service that validates and submits futures orders."""
        self.client = client

    def _round_to_tick(self, price: float, tick_size: float) -> float:
        """Round a raw price down to the nearest valid exchange tick size."""
        price_dec = Decimal(str(price))
        tick_dec = Decimal(str(tick_size))
        return float((price_dec // tick_dec) * tick_dec)

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """Validate inputs against Binance filters and place a futures order."""

        symbol = symbol.upper()
        side = validate_side(side)
        order_type = validate_order_type(order_type)
        quantity = validate_quantity(quantity)
        price = validate_price(price, order_type)
        stop_price = validate_stop_price(stop_price, order_type)

        mark_price = self.client.get_mark_price(symbol)
        filters = self.client.get_symbol_filters(symbol)

        logger.info(f"Mark price: {mark_price}")

        # --------------------------
        # Extract Filters
        # --------------------------

        price_filter = next(f for f in filters if f["filterType"] == "PRICE_FILTER")
        percent_filter = next(f for f in filters if f["filterType"] == "PERCENT_PRICE")
        notional_filter = next(
            f for f in filters if f["filterType"] == "MIN_NOTIONAL"
        )

        min_price = float(price_filter["minPrice"])
        max_price = float(price_filter["maxPrice"])
        tick_size = float(price_filter["tickSize"])

        multiplier_up = float(percent_filter["multiplierUp"])
        multiplier_down = float(percent_filter["multiplierDown"])

        min_notional = float(notional_filter["notional"])

        # --------------------------
        # Validate Notional
        # --------------------------

        notional = mark_price * quantity

        if notional < min_notional:
            raise ValueError(
                f"Order notional too small: {notional:.2f} USDT. "
                f"Minimum required: {min_notional} USDT"
            )

        # --------------------------
        # LIMIT / STOP_LIMIT Validation
        # --------------------------

        lower_bound = mark_price * multiplier_down
        upper_bound = mark_price * multiplier_up

        if order_type in ["LIMIT", "STOP_LIMIT"]:
            price = self._round_to_tick(price, tick_size)

            if not (min_price <= price <= max_price):
                raise ValueError(f"Price must be between {min_price} and {max_price}")

            if not (lower_bound <= price <= upper_bound):
                raise ValueError(
                    f"Price must be between {lower_bound:.2f} "
                    f"and {upper_bound:.2f} "
                    f"(mark price: {mark_price:.2f})"
                )

        if order_type == "STOP_LIMIT":
            stop_price = self._round_to_tick(stop_price, tick_size)

            if not (min_price <= stop_price <= max_price):
                raise ValueError(
                    f"Stop price must be between {min_price} and {max_price}"
                )

            if not (lower_bound <= stop_price <= upper_bound):
                raise ValueError(
                    f"Stop price must be between {lower_bound:.2f} "
                    f"and {upper_bound:.2f} "
                    f"(mark price: {mark_price:.2f})"
                )

        # --------------------------
        # Build Order Params
        # --------------------------

        order_params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP" if order_type == "STOP_LIMIT" else order_type,
            "quantity": quantity,
        }

        if order_type in ["LIMIT", "STOP_LIMIT"]:
            order_params["price"] = price
            order_params["timeInForce"] = "GTC"

        if order_type == "STOP_LIMIT":
            order_params["stopPrice"] = stop_price

        logger.info(f"Validated order params: {order_params}")

        response = self.client.create_order(**order_params)

        return {
            "response": response,
            "mark_price": mark_price,
            "notional": notional,
            "final_price": price if order_type in ["LIMIT", "STOP_LIMIT"] else None,
        }