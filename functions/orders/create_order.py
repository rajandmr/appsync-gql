import uuid
from decimal import Decimal
from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.info("createOrder event: %s", event)

    arguments = event.get("arguments") or {}
    identity = event.get("identity") or {}

    # When called via COGNITO_USER_POOLS, identity.sub holds the user's Cognito sub.
    customer_id = identity.get("sub") or identity.get("username") or "anonymous"

    item = {
        "orderId": str(uuid.uuid4()),
        "customerId": customer_id,
        # DynamoDB's high-level resource API requires Decimal for numbers.
        "total": Decimal(str(arguments["total"])),
        "status": arguments.get("status", "PENDING"),
    }

    orders = table("ORDERS_TABLE")
    orders.put_item(Item=item)
    logger.info("Created order %s for customer %s", item["orderId"], item["customerId"])
    return item