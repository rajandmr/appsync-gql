import uuid
from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

from utils.helper import logger, table
from utils.models import Order, OrderCreateEvent


@event_parser(model=OrderCreateEvent)
def handler(event: OrderCreateEvent, context: LambdaContext) -> dict[str, Any]:
    logger.info("createOrder", arguments=event.arguments.model_dump(mode="json"))

    assert event.identity is not None  # guaranteed by @aws_cognito_user_pools
    customer_id = event.identity["sub"]

    order = Order(
        orderId=str(uuid.uuid4()),
        customerId=customer_id,
        total=event.arguments.total,
        status=event.arguments.status,
    )

    table("ORDERS_TABLE").put_item(Item=order.model_dump())
    logger.info("created order", orderId=order.orderId, customerId=order.customerId)
    return order.model_dump()
