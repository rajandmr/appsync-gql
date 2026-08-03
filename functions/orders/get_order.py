from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> dict[str, Any] | None:
    logger.info("getOrder event: %s", event)

    arguments = event.get("arguments") or {}
    order_id = arguments["orderId"]

    orders = table("ORDERS_TABLE")
    response = orders.get_item(Key={"orderId": order_id})
    item = response.get("Item")
    if item is None:
        logger.info("Order %s not found", order_id)
        return None
    return item