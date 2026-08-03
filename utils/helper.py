import json
import logging
import os
from typing import Any

import boto3


def get_logger() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    return logger


logger = get_logger()


def log_event(logger: logging.Logger, event: dict[str, Any]) -> None:
    logger.info("Incoming event: %s", json.dumps(event, default=str))


def table(name_env: str = "TODOS_TABLE") -> Any:
    """Return a boto3 DynamoDB Table resource whose name comes from env.

    The reference repo exposes small helpers here; resolvers call this once at
    handler scope so each Lambda reads its table from its own environment.
    """
    return boto3.resource("dynamodb").Table(os.environ[name_env])


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """HTTP-style response helper (kept for parity with the reference repo).

    AppSync direct-Lambda resolvers do not require this HTTP envelope, but it is
    kept around for any HTTP-triggered helpers or tests that may be added later.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }