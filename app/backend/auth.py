"""Authentication helpers: password hashing, session, API keys."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import ApiKey, RoleEnum, User, get_db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def get_session_user_id(request: Request) -> int | None:
    return request.session.get("user_id")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter_by(id=user_id, active=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or inactive user")
    return user


def require_roles(*roles: RoleEnum):
    def _check(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Permission denied")
        return user

    return _check


superadmin_only = require_roles(RoleEnum.superadmin)
backoffice_or_above = require_roles(RoleEnum.superadmin, RoleEnum.backoffice)
any_role = require_roles(RoleEnum.superadmin, RoleEnum.backoffice, RoleEnum.operator)


def generate_api_key() -> str:
    return "mes_" + secrets.token_hex(24)


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class VirtualUser:
    id: Optional[int]
    username: str
    role: RoleEnum
    active: bool = True
    must_change_password: bool = False


def require_roles_or_api(*roles: RoleEnum):
    """Accept session cookie or X-API-Key / Authorization: Bearer."""

    def _check(request: Request, db: Session = Depends(get_db)):
        user_id = request.session.get("user_id")
        if user_id:
            user = db.query(User).filter_by(id=user_id, active=True).first()
            if user:
                if user.role not in roles:
                    raise HTTPException(403, "Permission denied")
                return user

        raw = request.headers.get("X-API-Key", "").strip()
        if not raw:
            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                raw = auth[7:].strip()

        if raw:
            digest = hash_api_key(raw)
            ak = db.query(ApiKey).filter_by(key_hash=digest, active=True).first()
            if ak:
                if ak.role not in roles:
                    raise HTTPException(403, "Permission denied: insufficient API key role")
                ak.last_used_at = datetime.utcnow()
                db.commit()
                return VirtualUser(
                    id=ak.created_by,
                    username=f"api:{ak.name}",
                    role=ak.role,
                )

        raise HTTPException(401, "Not authenticated")

    return _check


superadmin_or_api = require_roles_or_api(RoleEnum.superadmin)
backoffice_or_api = require_roles_or_api(RoleEnum.superadmin, RoleEnum.backoffice)
any_role_or_api = require_roles_or_api(
    RoleEnum.superadmin, RoleEnum.backoffice, RoleEnum.operator
)
