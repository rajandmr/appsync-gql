from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext
from utils.helper import logger, table
from utils.models import NoArgsEvent, Todo


@event_parser(model=NoArgsEvent)
def handler(event: NoArgsEvent, context: LambdaContext) -> list[dict[str, Any]]:
    logger.info("listTodos")

    response = table("TODOS_TABLE").scan()
    return [Todo.model_validate(item).model_dump() for item in response.get("Items", [])]
