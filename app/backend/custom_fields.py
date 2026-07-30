"""Custom fields: definitions + light validation rules (add-only schema)."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import FieldDefinition

ENTITIES = frozenset(
    {
        "customer",
        "product",
        "work_order",
        "work_order_line",
        "production_order",
        "operation_instance",
    }
)
FIELD_TYPES = frozenset({"string", "number", "boolean", "date", "select"})
KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def slugify_key(label: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", label.strip().lower())
    s = s.strip("_")
    if not s or not s[0].isalpha():
        s = "f_" + s
    return s[:63]


def list_definitions(
    db: Session, entity: str | None = None, active_only: bool = False
) -> list[FieldDefinition]:
    q = db.query(FieldDefinition)
    if entity:
        q = q.filter_by(entity=entity)
    if active_only:
        q = q.filter_by(active=True)
    return q.order_by(FieldDefinition.sort_order, FieldDefinition.id).all()


def _coerce_value(field_type: str, value: Any, options: list | None) -> Any:
    if value is None or value == "":
        return None
    if field_type == "string":
        return str(value)
    if field_type == "number":
        try:
            return float(value) if not isinstance(value, (int, float)) else float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, f"Invalid number: {value}") from exc
    if field_type == "boolean":
        if isinstance(value, bool):
            return value
        if str(value).lower() in {"1", "true", "yes", "si", "sì"}:
            return True
        if str(value).lower() in {"0", "false", "no"}:
            return False
        raise HTTPException(400, f"Invalid boolean: {value}")
    if field_type == "date":
        if isinstance(value, (date, datetime)):
            return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
        text = str(value).strip()
        try:
            date.fromisoformat(text[:10])
        except ValueError as exc:
            raise HTTPException(400, f"Invalid date (use YYYY-MM-DD): {value}") from exc
        return text[:10]
    if field_type == "select":
        text = str(value)
        opts = options or []
        if opts and text not in opts:
            raise HTTPException(400, f"Value '{text}' not in options {opts}")
        return text
    raise HTTPException(400, f"Unknown field type: {field_type}")


def merge_and_validate_custom_fields(
    db: Session,
    entity: str,
    incoming: dict | None,
    existing: dict | None = None,
    *,
    partial: bool = False,
) -> dict:
    """
    Merge incoming custom_fields onto existing and enforce light rules.

    - Unknown keys (not in definitions) are rejected
    - Inactive definitions: keep existing values, ignore new writes
    - Required active fields must be present after merge (unless partial update
      that does not touch custom_fields at all — caller passes incoming=None)
    """
    if incoming is None and partial:
        return dict(existing or {})

    defs = list_definitions(db, entity=entity, active_only=False)
    by_key = {d.key: d for d in defs}
    merged = dict(existing or {})

    if incoming:
        if not isinstance(incoming, dict):
            raise HTTPException(400, "custom_fields must be an object")
        for key, raw in incoming.items():
            d = by_key.get(key)
            if not d:
                raise HTTPException(400, f"Unknown custom field '{key}' for {entity}")
            if not d.active:
                raise HTTPException(
                    400,
                    f"Custom field '{key}' is inactive (cannot write; historical values kept)",
                )
            merged[key] = _coerce_value(d.field_type, raw, d.options)

    # Required checks against active definitions
    for d in defs:
        if not d.active or not d.required:
            continue
        val = merged.get(d.key)
        if val is None or val == "":
            raise HTTPException(400, f"Custom field '{d.key}' ({d.label}) is required")

    return merged
