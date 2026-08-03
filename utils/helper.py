"""Shared helpers for AppSync Lambda resolvers.

Uses AWS Lambda Powertools' structured `Logger` and a cached, typed DynamoDB
`Table` resource accessor powered by `mypy_boto3_dynamodb`.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import boto3
from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    # Type-only import: mypy_boto3_dynamodb is a dev dependency providing
    # stubs; the runtime only needs the unannotated boto3 Table resource.
    from mypy_boto3_dynamodb.service_resource import Table

logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME", "appsync-gql"))

# boto3.resource() builds a Session internally; reuse one across warm
# Lambda invocations instead of reconstructing on every call.
_dynamodb = boto3.resource("dynamodb")
_tables: dict[str, Table] = {}


def table(name_env: str = "TODOS_TABLE") -> Table:
    """Return a typed DynamoDB Table resource whose name comes from env.

    Resolvers call this once at handler scope so each Lambda reads its
    table from its own environment (e.g. ``TODOS_TABLE``/``ORDERS_TABLE``).
    Table objects are cached per (env-name) so warm invocations skip the
    lookup.
    """
    table_name = os.environ[name_env]
    cached = _tables.get(table_name)
    if cached is not None:
        return cached
    resolved = _dynamodb.Table(table_name)
    _tables[table_name] = resolved
    return resolved
