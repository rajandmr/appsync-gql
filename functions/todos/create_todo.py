import uuid
from typing import Any

from utils.helper import logger, table


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.info("createTodo event: %s", event)

    arguments = event.get("arguments") or {}
    title = arguments["title"]
    completed = bool(arguments.get("completed", False))

    item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "completed": completed,
    }

    todos = table("TODOS_TABLE")
    todos.put_item(Item=item)
    logger.info("Created todo %s", item["id"])
    return item