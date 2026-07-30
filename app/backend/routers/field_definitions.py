"""Custom field definitions — configured from UI, add-only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import any_role_or_api, superadmin_only
from custom_fields import ENTITIES, FIELD_TYPES, KEY_RE, list_definitions, slugify_key
from database import FieldDefinition, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/field-definitions", tags=["field-definitions"])

FIELDS = [
    "id",
    "entity",
    "key",
    "label",
    "field_type",
    "required",
    "options",
    "active",
    "sort_order",
    "created_at",
]


class FieldDefCreate(BaseModel):
    entity: str
    label: str = Field(min_length=1, max_length=128)
    key: str | None = None  # auto from label if omitted
    field_type: str = "string"
    required: bool = False
    options: list[str] | None = None
    sort_order: int = 0


class FieldDefPatch(BaseModel):
    label: str | None = None
    required: bool | None = None
    options: list[str] | None = None  # may only grow
    active: bool | None = None
    sort_order: int | None = None


@router.get("")
def list_field_definitions(
    entity: str | None = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    if entity and entity not in ENTITIES:
        raise HTTPException(400, f"Invalid entity. Allowed: {sorted(ENTITIES)}")
    rows = list_definitions(db, entity=entity, active_only=not include_inactive)
    return [model_to_dict(r, FIELDS) for r in rows]


@router.get("/entities")
def list_entities(_: User = Depends(any_role_or_api)):
    return sorted(ENTITIES)


@router.get("/{fid}")
def get_field_definition(
    fid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    row = db.query(FieldDefinition).filter_by(id=fid).first()
    if not row:
        raise HTTPException(404, "Field definition not found")
    return model_to_dict(row, FIELDS)


@router.post("")
def create_field_definition(
    payload: FieldDefCreate,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    if payload.entity not in ENTITIES:
        raise HTTPException(400, f"Invalid entity. Allowed: {sorted(ENTITIES)}")
    if payload.field_type not in FIELD_TYPES:
        raise HTTPException(400, f"Invalid field_type. Allowed: {sorted(FIELD_TYPES)}")
    key = (payload.key or slugify_key(payload.label)).strip().lower()
    if not KEY_RE.match(key):
        raise HTTPException(
            400,
            "key must be lowercase letter + [a-z0-9_], max 63 chars (or omit to auto-generate)",
        )
    if payload.field_type == "select":
        if not payload.options:
            raise HTTPException(400, "select fields require options")
    existing = (
        db.query(FieldDefinition)
        .filter_by(entity=payload.entity, key=key)
        .first()
    )
    if existing:
        raise HTTPException(
            400,
            f"Field '{key}' already exists for {payload.entity} "
            f"(reactivate it instead of creating a new one)",
        )
    row = FieldDefinition(
        entity=payload.entity,
        key=key,
        label=payload.label.strip(),
        field_type=payload.field_type,
        required=payload.required,
        options=list(payload.options) if payload.options else None,
        active=True,
        sort_order=payload.sort_order,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return model_to_dict(row, FIELDS)


@router.patch("/{fid}")
def patch_field_definition(
    fid: int,
    payload: FieldDefPatch,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    row = db.query(FieldDefinition).filter_by(id=fid).first()
    if not row:
        raise HTTPException(404, "Field definition not found")
    data = payload.model_dump(exclude_unset=True)
    if "options" in data and data["options"] is not None:
        if row.field_type != "select":
            raise HTTPException(400, "options only allowed on select fields")
        old = list(row.options or [])
        new = list(data["options"])
        # Add-only: every old option must remain
        missing = [o for o in old if o not in new]
        if missing:
            raise HTTPException(
                400,
                f"Cannot remove select options {missing} (add-only; would break historical data)",
            )
        row.options = new
        data.pop("options")
    if "label" in data and data["label"] is not None:
        row.label = data["label"].strip()
    if "required" in data and data["required"] is not None:
        row.required = data["required"]
    if "active" in data and data["active"] is not None:
        row.active = data["active"]
    if "sort_order" in data and data["sort_order"] is not None:
        row.sort_order = data["sort_order"]
    db.commit()
    db.refresh(row)
    return model_to_dict(row, FIELDS)


@router.delete("/{fid}")
def delete_field_definition(
    fid: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    row = db.query(FieldDefinition).filter_by(id=fid).first()
    if not row:
        raise HTTPException(404, "Field definition not found")
    raise HTTPException(
        405,
        "Deleting field definitions is not allowed (would break historical data). "
        "PATCH active=false to deactivate instead.",
    )
