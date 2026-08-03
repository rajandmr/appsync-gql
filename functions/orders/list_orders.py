from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> list[dict[str, Any]]:
    logger.info("listOrders event: %s", event)

    orders = table("ORDERS_TABLE")
    response = orders.scan()
    return response.get("Items", [])