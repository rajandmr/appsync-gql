from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from utils.helper import logger, table
from utils.models import Order, OrderIdEvent


@event_parser(model=OrderIdEvent)
def handler(event: OrderIdEvent, context: LambdaContext) -> dict[str, Any] | None:
    logger.info("getOrder", orderId=event.arguments.orderId)

    response = table("ORDERS_TABLE").get_item(Key={"orderId": event.arguments.orderId})
    item = response.get("Item")
    if item is None:
        logger.info("order not found", orderId=event.arguments.orderId)
        return None
    return Order.model_validate(item).model_dump()
