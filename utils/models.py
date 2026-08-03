"""Pydantic models for AppSync resolver events and DynamoDB domain entities.

These models are used together with `aws_lambda_powertools.utilities.parser.event_parser`
on every Lambda handler. AppSync direct-Lambda resolvers receive the AppSync
`$context` object verbatim as the Lambda `event` payload, so each handler parses
the whole event into a typed `AppSyncEvent[<ArgsModel>]`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_decimal(v: Any) -> Decimal:
    """Coerce a numeric input to Decimal via str() to avoid binary-float drift.

    AppSync ships floats on the wire; DynamoDB needs Decimal. `str(v)`
    preserves source precision (e.g. 19.99 -> "19.99" -> Decimal("19.99")).
    """
    return Decimal(str(v))


class AppSyncEvent[ArgsT](BaseModel):
    """Typed envelope for an AppSync direct-Lambda resolver event.

    AppSync populates `arguments` from the GraphQL field arguments and
    `identity` with the caller identity (Cognito sub/username when authed).
    Extra contextual fields (`info`, `source`, `stash`, `prev`, ...) are
    ignored to keep the model stable across AppSync schema additions.
    """

    model_config = ConfigDict(extra="ignore")

    arguments: ArgsT
    identity: dict[str, Any] | None = None
    info: dict[str, Any] | None = None
    source: dict[str, Any] | None = None


# --------------------------------------------------------------------------- #
# Todos
# --------------------------------------------------------------------------- #


class Todo(BaseModel):
    """A Todo row in DynamoDB."""

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    completed: bool = False


class TodoCreateArgs(BaseModel):
    """Arguments for the `createTodo` mutation."""

    model_config = ConfigDict(extra="forbid")

    title: str
    completed: bool = False


class TodoUpdateArgs(BaseModel):
    """Arguments for the `updateTodo` mutation. All optional fields can be
    omitted on the wire, so they default to `None` and the resolver decides
    whether to write them.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str | None = None
    completed: bool | None = None


class TodoIdArgs(BaseModel):
    """Arguments for `getTodo` / `deleteTodo` (single id)."""

    model_config = ConfigDict(extra="forbid")

    id: str


# --------------------------------------------------------------------------- #
# Orders
# --------------------------------------------------------------------------- #


class Order(BaseModel):
    """An Order row in DynamoDB."""

    model_config = ConfigDict(extra="ignore")

    orderId: str
    customerId: str
    total: Decimal
    status: str = "PENDING"

    @field_validator("total", mode="before")
    @classmethod
    def _coerce_total(cls, v: Any) -> Decimal:
        return _coerce_decimal(v)


class OrderCreateArgs(BaseModel):
    """Arguments for the `createOrder` mutation."""

    model_config = ConfigDict(extra="forbid")

    total: Decimal = Field(..., description="Order total. Coerced to Decimal.")
    status: str = "PENDING"

    @field_validator("total", mode="before")
    @classmethod
    def _coerce_total(cls, v: Any) -> Decimal:
        return _coerce_decimal(v)


class OrderIdArgs(BaseModel):
    """Arguments for `getOrder`."""

    model_config = ConfigDict(extra="forbid")

    orderId: str


# Concrete event aliases for clarity in handler signatures.
TodoCreateEvent = AppSyncEvent[TodoCreateArgs]
TodoUpdateEvent = AppSyncEvent[TodoUpdateArgs]
TodoIdEvent = AppSyncEvent[TodoIdArgs]
OrderCreateEvent = AppSyncEvent[OrderCreateArgs]
OrderIdEvent = AppSyncEvent[OrderIdArgs]
NoArgsEvent = AppSyncEvent[dict[str, Any]]
