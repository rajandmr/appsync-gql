import uuid
from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from utils.helper import logger, table
from utils.models import Todo, TodoCreateEvent


@event_parser(model=TodoCreateEvent)
def handler(event: TodoCreateEvent, context: LambdaContext) -> dict[str, Any]:
    logger.info("createTodo", arguments=event.arguments.model_dump())

    todo = Todo(
        id=str(uuid.uuid4()),
        title=event.arguments.title,
        completed=event.arguments.completed,
    )

    table("TODOS_TABLE").put_item(Item=todo.model_dump())
    logger.info("created todo", id=todo.id)
    return todo.model_dump()
