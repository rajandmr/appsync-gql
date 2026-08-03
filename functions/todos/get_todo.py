from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> dict[str, Any] | None:
    logger.info("getTodo event: %s", event)

    arguments = event.get("arguments") or {}
    todo_id = arguments["id"]

    todos = table("TODOS_TABLE")
    response = todos.get_item(Key={"id": todo_id})
    item = response.get("Item")
    if item is None:
        logger.info("Todo %s not found", todo_id)
        return None
    return item