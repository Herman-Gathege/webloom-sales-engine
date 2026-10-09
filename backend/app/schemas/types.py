"""Shared field types for response models."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import PlainSerializer


def _as_utc_iso8601(value: datetime) -> str:
    """The contract says ISO 8601, UTC — for every timestamp, whatever the
    database session's timezone happens to be."""
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[datetime, PlainSerializer(_as_utc_iso8601, return_type=str)]
