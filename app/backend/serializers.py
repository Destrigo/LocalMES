"""
Generic helpers for LocalMES API schemas and CRUD serialization.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def model_to_dict(obj: Any, fields: list[str]) -> dict:
    return {name: serialize_value(getattr(obj, name)) for name in fields}
