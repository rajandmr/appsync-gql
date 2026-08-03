from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> list[dict[str, Any]]:
    logger.info("listTodos event: %s", event)

    todos = table("TODOS_TABLE")
    response = todos.scan()
    return response.get("Items", [])