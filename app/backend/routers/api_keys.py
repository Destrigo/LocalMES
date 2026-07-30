"""API key management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import generate_api_key, hash_api_key, superadmin_only
from database import ApiKey, RoleEnum, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

FIELDS = ["id", "name", "role", "active", "created_at", "last_used_at", "created_by"]


class ApiKeyCreate(BaseModel):
    name: str
    role: RoleEnum = RoleEnum.backoffice


class ApiKeyPatch(BaseModel):
    active: bool | None = None
    name: str | None = None


@router.get("")
def list_keys(db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    return [
        model_to_dict(ak, FIELDS)
        for ak in db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    ]


@router.get("/{key_id}")
def get_key(key_id: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    ak = db.query(ApiKey).filter_by(id=key_id).first()
    if not ak:
        raise HTTPException(404, "API key not found")
    return model_to_dict(ak, FIELDS)


@router.post("")
def create_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(superadmin_only),
):
    raw = generate_api_key()
    ak = ApiKey(
        name=payload.name,
        key_hash=hash_api_key(raw),
        role=payload.role,
        active=True,
        created_by=user.id,
    )
    db.add(ak)
    db.commit()
    db.refresh(ak)
    return {**model_to_dict(ak, FIELDS), "key": raw}


@router.patch("/{key_id}")
def patch_key(
    key_id: int,
    payload: ApiKeyPatch,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    ak = db.query(ApiKey).filter_by(id=key_id).first()
    if not ak:
        raise HTTPException(404, "API key not found")
    if payload.active is not None:
        ak.active = payload.active
    if payload.name is not None:
        ak.name = payload.name
    db.commit()
    return model_to_dict(ak, FIELDS)


@router.delete("/{key_id}")
def delete_key(
    key_id: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    ak = db.query(ApiKey).filter_by(id=key_id).first()
    if not ak:
        raise HTTPException(404, "API key not found")
    db.delete(ak)
    db.commit()
    return {"ok": True}
