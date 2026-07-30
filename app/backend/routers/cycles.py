"""Production cycles (routings)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_above
from database import Cycle, CycleStep, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/cycles", tags=["cycles"])

CYCLE_FIELDS = ["id", "name", "description", "active"]
STEP_FIELDS = ["id", "cycle_id", "operation_id", "position"]


class StepIn(BaseModel):
    operation_id: int
    position: int = 0


class CycleIn(BaseModel):
    name: str
    description: str | None = None
    active: bool = True
    steps: list[StepIn] = Field(default_factory=list)


class CyclePatch(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None
    steps: list[StepIn] | None = None


def _cycle_dict(c: Cycle) -> dict:
    data = model_to_dict(c, CYCLE_FIELDS)
    data["steps"] = [model_to_dict(s, STEP_FIELDS) for s in c.steps]
    return data


@router.get("")
def list_cycles(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    return [_cycle_dict(c) for c in db.query(Cycle).order_by(Cycle.name).all()]


@router.get("/{cid}")
def get_cycle(cid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    c = db.query(Cycle).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Cycle not found")
    return _cycle_dict(c)


@router.post("")
def create_cycle(
    payload: CycleIn, db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)
):
    c = Cycle(name=payload.name, description=payload.description, active=payload.active)
    db.add(c)
    db.flush()
    for step in payload.steps:
        db.add(
            CycleStep(
                cycle_id=c.id,
                operation_id=step.operation_id,
                position=step.position,
            )
        )
    db.commit()
    db.refresh(c)
    return _cycle_dict(c)


@router.patch("/{cid}")
def patch_cycle(
    cid: int,
    payload: CyclePatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_above),
):
    c = db.query(Cycle).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Cycle not found")
    data = payload.model_dump(exclude_unset=True)
    steps = data.pop("steps", None)
    for k, v in data.items():
        setattr(c, k, v)
    if steps is not None:
        for s in list(c.steps):
            db.delete(s)
        db.flush()
        for step in steps:
            db.add(
                CycleStep(
                    cycle_id=c.id,
                    operation_id=step["operation_id"],
                    position=step["position"],
                )
            )
    db.commit()
    db.refresh(c)
    return _cycle_dict(c)


@router.delete("/{cid}")
def delete_cycle(
    cid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)
):
    c = db.query(Cycle).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Cycle not found")
    db.delete(c)
    db.commit()
    return {"ok": True}
