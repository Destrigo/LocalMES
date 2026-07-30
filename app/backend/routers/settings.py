"""Settings and local backup (manual + scheduled)."""

from __future__ import annotations

import glob
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import superadmin_only
from database import BASE_DIR, BackupLog, SessionLocal, Setting, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/settings", tags=["settings"])

SETTING_FIELDS = ["key", "value"]
BACKUP_FIELDS = ["id", "timestamp", "path", "result", "message"]
ALLOWED_KEYS = {
    "company_name",
    "logo_path",
    "backup_dir",
    "backup_enabled",
    "language_default",
}

_backup_timer: threading.Timer | None = None
_DB_FILE = os.path.join(BASE_DIR, "database.db")


def _run_backup_copy(dest_dir: str) -> tuple[bool, str]:
    try:
        os.makedirs(dest_dir, exist_ok=True)
        name = f"localmes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        dest = os.path.join(dest_dir, name)
        shutil.copy2(_DB_FILE, dest)
        backups = sorted(glob.glob(os.path.join(dest_dir, "localmes_*.db")))
        while len(backups) > 48:
            os.remove(backups.pop(0))
        return True, dest
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _backup_tick():
    db = SessionLocal()
    try:
        enabled = db.query(Setting).filter_by(key="backup_enabled").first()
        path = db.query(Setting).filter_by(key="backup_dir").first()
        if enabled and enabled.value == "true" and path and path.value:
            ok, msg = _run_backup_copy(path.value)
            db.add(
                BackupLog(
                    path=msg if ok else None,
                    result="ok" if ok else "error",
                    message=None if ok else msg,
                )
            )
            db.commit()
    finally:
        db.close()
    _schedule_backup(1800)


def _schedule_backup(seconds: float = 1800):
    global _backup_timer
    _backup_timer = threading.Timer(seconds, _backup_tick)
    _backup_timer.daemon = True
    _backup_timer.start()


def start_backup_scheduler():
    _schedule_backup(1800)


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
    if not Path(_DB_FILE).exists():
        raise HTTPException(400, "database.db not found")
    ok, msg = _run_backup_copy(dest_dir)
    log = BackupLog(
        path=msg if ok else None,
        result="ok" if ok else "error",
        message=None if ok else msg,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    if not ok:
        raise HTTPException(500, f"Backup failed: {msg}")
    return model_to_dict(log, BACKUP_FIELDS)


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    _: User = Depends(superadmin_only),
):
    static = Path(BASE_DIR) / "static"
    static.mkdir(exist_ok=True)
    dest = static / "logo.png"
    dest.write_bytes(await file.read())
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
    if key not in ALLOWED_KEYS:
        raise HTTPException(400, f"Invalid setting key. Allowed: {sorted(ALLOWED_KEYS)}")
    s = db.query(Setting).filter_by(key=key).first()
    if not s:
        s = Setting(key=key, value=payload.value)
        db.add(s)
    else:
        s.value = payload.value
    db.commit()
    return model_to_dict(s, SETTING_FIELDS)
