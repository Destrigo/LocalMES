"""BOM and report endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_api, backoffice_or_above
from database import Bom, Downtime, OperationInstance, ProductionOrder, User, get_db
from serializers import model_to_dict

boms_router = APIRouter(prefix="/boms", tags=["boms"])
reports_router = APIRouter(prefix="/reports", tags=["reports"])

BOM_FIELDS = [
    "id",
    "parent_code",
    "parent_description",
    "component_code",
    "component_description",
    "quantity",
    "cost",
]


class BomIn(BaseModel):
    parent_code: str
    parent_description: str | None = None
    component_code: str
    component_description: str | None = None
    quantity: float = 1.0
    cost: float | None = None


class BomPatch(BaseModel):
    parent_code: str | None = None
    parent_description: str | None = None
    component_code: str | None = None
    component_description: str | None = None
    quantity: float | None = None
    cost: float | None = None


@boms_router.get("")
def list_boms(
    parent_code: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    q = db.query(Bom)
    if parent_code:
        q = q.filter_by(parent_code=parent_code)
    return [model_to_dict(b, BOM_FIELDS) for b in q.all()]


@boms_router.get("/{bid}")
def get_bom(bid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    b = db.query(Bom).filter_by(id=bid).first()
    if not b:
        raise HTTPException(404, "BOM row not found")
    return model_to_dict(b, BOM_FIELDS)


@boms_router.post("")
def create_bom(
    payload: BomIn, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    b = Bom(**payload.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return model_to_dict(b, BOM_FIELDS)


@boms_router.patch("/{bid}")
def patch_bom(
    bid: int,
    payload: BomPatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    b = db.query(Bom).filter_by(id=bid).first()
    if not b:
        raise HTTPException(404, "BOM row not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    return model_to_dict(b, BOM_FIELDS)


@boms_router.delete("/{bid}")
def delete_bom(
    bid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    b = db.query(Bom).filter_by(id=bid).first()
    if not b:
        raise HTTPException(404, "BOM row not found")
    db.delete(b)
    db.commit()
    return {"ok": True}


@reports_router.get("/production-orders")
def report_orders(db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)):
    return [
        model_to_dict(
            o,
            [
                "id",
                "order_number",
                "customer_name",
                "product_id",
                "free_code",
                "product_description",
                "quantity_ordered",
                "status",
                "created_by",
                "created_at",
                "updated_at",
                "comment",
            ],
        )
        for o in db.query(ProductionOrder).order_by(ProductionOrder.created_at.desc()).all()
    ]


@reports_router.get("/operation-instances")
def report_instances(db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)):
    return [
        model_to_dict(
            i,
            [
                "id",
                "order_id",
                "operation_id",
                "line_id",
                "operator_count",
                "status",
                "started_by",
                "quantity_produced",
                "lot_code",
                "started_at",
                "ended_at",
            ],
        )
        for i in db.query(OperationInstance).order_by(OperationInstance.started_at.desc()).all()
    ]


@reports_router.get("/downtimes")
def report_downtimes(db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)):
    return [
        model_to_dict(d, ["id", "instance_id", "reason_id", "started_at", "ended_at"])
        for d in db.query(Downtime).order_by(Downtime.started_at.desc()).all()
    ]
