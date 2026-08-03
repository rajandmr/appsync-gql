from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> dict[str, Any] | None:
    logger.info("updateTodo event: %s", event)

    arguments = event.get("arguments") or {}
    todo_id = arguments["id"]

    update_expressions: list[str] = []
    expression_attribute_names: dict[str, str] = {}
    expression_attribute_values: dict[str, Any] = {}

    if arguments.get("title") is not None:
        update_expressions.append("#title = :title")
        expression_attribute_names["#title"] = "title"
        expression_attribute_values[":title"] = arguments["title"]

    if arguments.get("completed") is not None:
        update_expressions.append("#completed = :completed")
        expression_attribute_names["#completed"] = "completed"
        expression_attribute_values[":completed"] = bool(arguments["completed"])

    todos = table("TODOS_TABLE")
    if not update_expressions:
        logger.info("updateTodo called with no updatable fields for %s", todo_id)
        return todos.get_item(Key={"id": todo_id}).get("Item")

    response = todos.update_item(
        Key={"id": todo_id},
        UpdateExpression="SET " + ", ".join(update_expressions),
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )
    return response.get("Attributes")