"""User management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import hash_password, superadmin_only
from database import RoleEnum, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/users", tags=["users"])

FIELDS = [
    "id",
    "username",
    "role",
    "active",
    "must_change_password",
    "created_at",
]


class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=6)
    role: RoleEnum = RoleEnum.operator


class UserPatch(BaseModel):
    role: RoleEnum | None = None
    active: bool | None = None


class ResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=6)


@router.get("")
def list_users(db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    return [model_to_dict(u, FIELDS) for u in db.query(User).order_by(User.username).all()]


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return model_to_dict(user, FIELDS)


@router.post("")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    if db.query(User).filter_by(username=payload.username).first():
        raise HTTPException(400, "Username already exists")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=True,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return model_to_dict(user, FIELDS)


@router.patch("/{user_id}")
def patch_user(
    user_id: int,
    payload: UserPatch,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if payload.role is not None:
        user.role = payload.role
    if payload.active is not None:
        user.active = payload.active
    db.commit()
    return model_to_dict(user, FIELDS)


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: ResetPasswordIn,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = True
    db.commit()
    return {"ok": True}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(superadmin_only),
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current.id:
        raise HTTPException(400, "Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"ok": True}
