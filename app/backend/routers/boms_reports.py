"""BOM CRUD and report export endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_api, backoffice_or_above
from database import Bom, Downtime, OperationInstance, ProductionOrder, User, get_db
from io_utils import pdf_table_response, xlsx_response
from serializers import model_to_dict, serialize_value

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
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    q = db.query(Bom)
    if parent_code:
        q = q.filter_by(parent_code=parent_code)
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    return {
        "items": [model_to_dict(b, BOM_FIELDS) for b in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


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


def _order_rows(db: Session):
    return [
        [
            o.order_number,
            o.customer_name,
            o.free_code or "",
            o.product_description,
            o.quantity_ordered,
            serialize_value(o.status),
            serialize_value(o.created_at),
            serialize_value(o.updated_at),
        ]
        for o in db.query(ProductionOrder).order_by(ProductionOrder.created_at.desc()).all()
    ]


def _instance_rows(db: Session):
    return [
        [
            i.order_id,
            i.operation_id,
            i.line_id,
            i.operator_count,
            serialize_value(i.status),
            i.quantity_produced or "",
            i.lot_code or "",
            serialize_value(i.started_at),
            serialize_value(i.ended_at),
        ]
        for i in db.query(OperationInstance).order_by(OperationInstance.started_at.desc()).all()
    ]


def _downtime_rows(db: Session):
    return [
        [
            d.id,
            d.instance_id,
            d.reason_id,
            serialize_value(d.started_at),
            serialize_value(d.ended_at),
        ]
        for d in db.query(Downtime).order_by(Downtime.started_at.desc()).all()
    ]


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


@reports_router.get("/export-excel")
def export_excel(db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)):
    return xlsx_response(
        {
            "ProductionOrders": (
                [
                    "Order Number",
                    "Customer",
                    "Free Code",
                    "Description",
                    "Qty",
                    "Status",
                    "Created",
                    "Updated",
                ],
                _order_rows(db),
            ),
            "OperationInstances": (
                [
                    "Order ID",
                    "Operation ID",
                    "Line ID",
                    "Operators",
                    "Status",
                    "Qty",
                    "Lot",
                    "Started",
                    "Ended",
                ],
                _instance_rows(db),
            ),
            "Downtimes": (
                ["ID", "Instance ID", "Reason ID", "Started", "Ended"],
                _downtime_rows(db),
            ),
        },
        filename="localmes_report.xlsx",
    )


@reports_router.get("/export-pdf")
def export_pdf(db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)):
    return pdf_table_response(
        title="LocalMES Production Orders",
        headers=["Order", "Customer", "Description", "Qty", "Status", "Created"],
        rows=[
            [r[0], r[1], r[3], r[4], r[5], r[6]]
            for r in _order_rows(db)
        ],
        filename="localmes_report.pdf",
    )
