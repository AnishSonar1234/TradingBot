def validate_side(side: str):
    """Normalize and validate the order side (BUY or SELL)."""
    side = side.upper()
    if side not in ["BUY", "SELL"]:
        raise ValueError("Side must be BUY or SELL")
    return side


def validate_order_type(order_type: str):
    """Normalize and validate supported order types."""
    order_type = order_type.upper()
    if order_type not in ["MARKET", "LIMIT", "STOP_LIMIT"]:
        raise ValueError("Order type must be MARKET, LIMIT, or STOP_LIMIT")
    return order_type


def validate_quantity(quantity: float):
    """Ensure the requested order quantity is strictly positive."""
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")
    return quantity


def validate_price(price, order_type):
    """Validate and require limit price for price-based order types."""
    if order_type in ["LIMIT", "STOP_LIMIT"] and price is None:
        raise ValueError("Price is required for LIMIT and STOP_LIMIT orders")
    return price


def validate_stop_price(stop_price, order_type):
    """Validate and require stop trigger price for STOP_LIMIT orders."""
    if order_type == "STOP_LIMIT" and stop_price is None:
        raise ValueError("stop_price is required for STOP_LIMIT orders")
    return stop_price