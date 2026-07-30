"""Auth endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user, hash_password, verify_password
from database import User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/auth", tags=["auth"])

USER_FIELDS = [
    "id",
    "username",
    "role",
    "active",
    "must_change_password",
    "created_at",
]


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=payload.username, active=True).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    request.session["user_id"] = user.id
    return model_to_dict(user, USER_FIELDS)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return model_to_dict(user, USER_FIELDS)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    return {"ok": True}
