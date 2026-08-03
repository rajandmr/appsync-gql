from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> dict[str, Any] | None:
    logger.info("deleteTodo event: %s", event)

    arguments = event.get("arguments") or {}
    todo_id = arguments["id"]

    todos = table("TODOS_TABLE")
    response = todos.delete_item(Key={"id": todo_id}, ReturnValues="ALL_OLD")
    item = response.get("Attributes")
    if item is None:
        logger.info("Todo %s not found on delete", todo_id)
        return None
    return item