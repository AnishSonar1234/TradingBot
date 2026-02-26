import argparse
import logging
from bot.client import BinanceFuturesClient
from bot.orders import OrderService
from bot.logging_config import setup_logging


def _display(value, default="N/A"):
    """Pretty-print helper: replace None/empty strings with a default label."""
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    return value


def main():
    """Entry point for the CLI trading tool."""
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Binance Futures Testnet Trading Bot"
    )

    parser.add_argument("--symbol", required=True)
    parser.add_argument("--side", required=True)
    parser.add_argument("--type", required=True)
    parser.add_argument("--quantity", type=float, required=True)
    parser.add_argument("--price", type=float)
    parser.add_argument("--stop-price", type=float)

    args = parser.parse_args()

    try:
        client = BinanceFuturesClient()
        service = OrderService(client)

        print("\n==============================")
        print("ORDER REQUEST")
        print("==============================")
        print(f"Symbol   : {args.symbol.upper()}")
        print(f"Side     : {args.side.upper()}")
        print(f"Type     : {args.type.upper()}")
        print(f"Quantity : {args.quantity}")
        if args.type.upper() == "LIMIT":
            print(f"Input Price : {args.price}")
        if args.type.upper() == "STOP_LIMIT":
            print(f"Input Price     : {args.price}")
            print(f"Input Stop Price: {args.stop_price}")

        result = service.place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )

        response = result["response"]

        print("\n==============================")
        print("ORDER RESPONSE")
        print("==============================")

        # Prefer standard futures order fields; fall back to conditional (STOP) fields
        order_id = response.get("orderId") or response.get("algoId")
        status = response.get("status") or response.get("algoStatus")

        print(f"Order ID     : {_display(order_id)}")
        print(f"Status       : {_display(status)}")

        # Only show execution details when they exist in the response
        if "executedQty" in response:
            print(f"ExecutedQty  : {_display(response.get('executedQty'))}")
        if "avgPrice" in response:
            print(f"Avg Price    : {_display(response.get('avgPrice'))}")

        print(f"Mark Price   : {result['mark_price']:.2f}")
        print(f"Notional     : {result['notional']:.2f} USDT")

        if result["final_price"]:
            print(f"Final Price  : {result['final_price']}")

        print("\nOrder placed successfully")

    except Exception as e:
        logger.exception("Order failed")
        print("\nOrder Failed")
        print(str(e))


if __name__ == "__main__":
    main()