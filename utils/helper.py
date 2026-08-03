"""Shared helpers for AppSync Lambda resolvers.

Uses AWS Lambda Powertools' structured `Logger` and a typed DynamoDB
`Table` resource accessor powered by `mypy_boto3_dynamodb`.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

import boto3

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    # Type-only import: mypy_boto3_dynamodb is a dev dependency providing
    # stubs; the runtime only needs the unannotated boto3 Table resource.
    from mypy_boto3_dynamodb.service_resource import Table

logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME", "appsync-gql"))


def log_event(event: dict[str, Any]) -> None:
    """Pretty-print an incoming event for debugging at INFO level."""
    logger.info("incoming_event", event=json.dumps(event, default=str))


def table(name_env: str = "TODOS_TABLE") -> Table:
    """Return a typed DynamoDB Table resource whose name comes from env.

    Resolvers call this once at handler scope so each Lambda reads its
    table from its own environment (e.g. ``TODOS_TABLE``/``ORDERS_TABLE``).
    """
    return boto3.resource("dynamodb").Table(os.environ[name_env])


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """HTTP-style response helper (kept for parity / HTTP-triggered helpers).

    AppSync direct-Lambda resolvers do not require this HTTP envelope, but
    it is kept around for any HTTP-triggered helpers or tests added later.
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
