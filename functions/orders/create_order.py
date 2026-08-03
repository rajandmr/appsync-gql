import uuid
from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext

from utils.helper import logger, table
from utils.models import Order, OrderCreateEvent


@event_parser(model=OrderCreateEvent)
def handler(event: OrderCreateEvent, context: LambdaContext) -> dict[str, Any]:
    logger.info("createOrder", arguments=event.arguments.model_dump(mode="json"))

    if event.identity is None:
        # @aws_cognito_user_pools on the schema should make this unreachable,
        # but guard explicitly rather than relying on assert (stripped by -O).
        raise RuntimeError("createOrder requires an authenticated Cognito identity")

    customer_id = event.identity["sub"]

    order = Order(
        orderId=str(uuid.uuid4()),
        customerId=customer_id,
        total=event.arguments.total,
        status=event.arguments.status,
    )

    payload = order.model_dump()
    table("ORDERS_TABLE").put_item(Item=payload)
    logger.info("created order", orderId=order.orderId, customerId=order.customerId)
    return payload
