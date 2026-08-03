from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from utils.helper import logger, table
from utils.models import Todo, TodoIdEvent


@event_parser(model=TodoIdEvent)
def handler(event: TodoIdEvent, context: LambdaContext) -> dict[str, Any] | None:
    logger.info("deleteTodo", id=event.arguments.id)

    response = table("TODOS_TABLE").delete_item(
        Key={"id": event.arguments.id}, ReturnValues="ALL_OLD"
    )
    item = response.get("Attributes")
    if item is None:
        logger.info("todo not found on delete", id=event.arguments.id)
        return None
    return Todo.model_validate(item).model_dump()
