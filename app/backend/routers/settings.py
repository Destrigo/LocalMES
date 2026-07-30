"""Settings and local backup."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import superadmin_only
from database import BASE_DIR, BackupLog, Setting, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/settings", tags=["settings"])

SETTING_FIELDS = ["key", "value"]
BACKUP_FIELDS = ["id", "timestamp", "path", "result", "message"]


class SettingPut(BaseModel):
    value: str | None = None


@router.get("")
def list_settings(db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    return [model_to_dict(s, SETTING_FIELDS) for s in db.query(Setting).all()]


@router.get("/backup/logs")
def backup_logs(db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    return [
        model_to_dict(x, BACKUP_FIELDS)
        for x in db.query(BackupLog).order_by(BackupLog.timestamp.desc()).limit(100).all()
    ]


@router.post("/backup/run")
def run_backup(db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    setting = db.query(Setting).filter_by(key="backup_dir").first()
    dest_dir = (setting.value if setting else None) or os.environ.get("MES_BACKUP_DIR", "")
    if not dest_dir:
        raise HTTPException(400, "backup_dir is not configured")
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    src = Path(BASE_DIR) / "database.db"
    if not src.exists():
        raise HTTPException(400, "database.db not found")
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = Path(dest_dir) / f"localmes_{stamp}.db"
    try:
        shutil.copy2(src, dest)
        log = BackupLog(path=str(dest), result="ok", message="Backup completed")
    except Exception as exc:  # noqa: BLE001
        log = BackupLog(path=str(dest), result="error", message=str(exc))
        db.add(log)
        db.commit()
        raise HTTPException(500, f"Backup failed: {exc}") from exc
    db.add(log)
    db.commit()
    return model_to_dict(log, BACKUP_FIELDS)


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    _: User = Depends(superadmin_only),
):
    static = Path(BASE_DIR) / "static"
    static.mkdir(exist_ok=True)
    dest = static / "logo.png"
    content = await file.read()
    dest.write_bytes(content)
    return {"ok": True, "path": "/static/logo.png"}


@router.get("/{key}")
def get_setting(
    key: str, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    s = db.query(Setting).filter_by(key=key).first()
    if not s:
        raise HTTPException(404, "Setting not found")
    return model_to_dict(s, SETTING_FIELDS)


@router.put("/{key}")
def put_setting(
    key: str,
    payload: SettingPut,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    s = db.query(Setting).filter_by(key=key).first()
    if not s:
        s = Setting(key=key, value=payload.value)
        db.add(s)
    else:
        s.value = payload.value
    db.commit()
    return model_to_dict(s, SETTING_FIELDS)
