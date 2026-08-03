from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from utils.helper import logger, table
from utils.models import Todo, TodoUpdateEvent


@event_parser(model=TodoUpdateEvent)
def handler(event: TodoUpdateEvent, context: LambdaContext) -> dict[str, Any] | None:
    args = event.arguments
    logger.info("updateTodo", id=args.id)

    update_expressions: list[str] = []
    expression_attribute_names: dict[str, str] = {}
    expression_attribute_values: dict[str, Any] = {}

    if args.title is not None:
        update_expressions.append("#title = :title")
        expression_attribute_names["#title"] = "title"
        expression_attribute_values[":title"] = args.title

    if args.completed is not None:
        update_expressions.append("#completed = :completed")
        expression_attribute_names["#completed"] = "completed"
        expression_attribute_values[":completed"] = args.completed

    todos = table("TODOS_TABLE")
    if not update_expressions:
        logger.info("updateTodo called with no updatable fields", id=args.id)
        item = todos.get_item(Key={"id": args.id}).get("Item")
        return None if item is None else Todo.model_validate(item).model_dump()

    response = todos.update_item(
        Key={"id": args.id},
        UpdateExpression="SET " + ", ".join(update_expressions),
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )
    attrs = response.get("Attributes")
    return None if attrs is None else Todo.model_validate(attrs).model_dump()
