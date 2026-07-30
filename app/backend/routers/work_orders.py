"""Work orders (customer jobs) with lines and components."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_api
from custom_fields import merge_and_validate_custom_fields
from database import (
    Cycle,
    EventType,
    OrderEvent,
    Product,
    ProductionOrder,
    ProductionOrderOperation,
    ProductionOrderStatus,
    User,
    WorkOrder,
    WorkOrderLine,
    WorkOrderLineComponent,
    get_db,
)
from serializers import model_to_dict

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

WO_FIELDS = [
    "id",
    "sequence_number",
    "customer_id",
    "customer_reference",
    "comment",
    "status",
    "created_at",
    "due_date",
    "source_file",
    "external_id",
    "external_doc_number",
    "custom_fields",
]
LINE_FIELDS = [
    "id",
    "work_order_id",
    "product_id",
    "free_code",
    "description",
    "quantity",
    "unit_value",
    "proposed_cycle_json",
    "notes",
    "line_ref",
    "external_id",
    "qty_fulfilled",
    "custom_fields",
]
COMP_FIELDS = ["id", "line_id", "code", "description", "quantity"]


class ComponentIn(BaseModel):
    code: str | None = None
    description: str
    quantity: str


class LineIn(BaseModel):
    product_id: int | None = None
    free_code: str | None = None
    description: str
    quantity: int = 1
    unit_value: str | None = None
    proposed_cycle_json: list | dict | None = None
    notes: str | None = None
    line_ref: str | None = None
    external_id: str | None = None
    qty_fulfilled: int | None = None
    custom_fields: dict | None = None
    components: list[ComponentIn] = Field(default_factory=list)


class WorkOrderIn(BaseModel):
    customer_id: int
    customer_reference: str | None = None
    comment: str | None = None
    status: str = "draft"
    due_date: datetime | None = None
    source_file: str | None = None
    external_id: str | None = None
    external_doc_number: str | None = None
    custom_fields: dict | None = None
    lines: list[LineIn] = Field(default_factory=list)


class WorkOrderPatch(BaseModel):
    customer_id: int | None = None
    customer_reference: str | None = None
    comment: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    source_file: str | None = None
    external_id: str | None = None
    external_doc_number: str | None = None
    custom_fields: dict | None = None


class LinePatch(BaseModel):
    product_id: int | None = None
    free_code: str | None = None
    description: str | None = None
    quantity: int | None = None
    unit_value: str | None = None
    proposed_cycle_json: list | dict | None = None
    notes: str | None = None
    line_ref: str | None = None
    external_id: str | None = None
    qty_fulfilled: int | None = None
    custom_fields: dict | None = None


def _line_dict(line: WorkOrderLine) -> dict:
    data = model_to_dict(line, LINE_FIELDS)
    data["components"] = [model_to_dict(c, COMP_FIELDS) for c in line.components]
    return data


def _wo_dict(wo: WorkOrder) -> dict:
    data = model_to_dict(wo, WO_FIELDS)
    data["customer_name"] = wo.customer.company_name if wo.customer else None
    data["lines"] = [_line_dict(l) for l in wo.lines]
    return data


def _next_sequence(db: Session) -> int:
    current = db.query(func.max(WorkOrder.sequence_number)).scalar()
    return (current or 0) + 1


@router.get("")
def list_work_orders(
    status: str | None = Query(None),
    customer_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    q = db.query(WorkOrder)
    if status:
        q = q.filter_by(status=status)
    if customer_id:
        q = q.filter_by(customer_id=customer_id)
    rows = q.order_by(WorkOrder.sequence_number.desc()).offset(offset).limit(limit).all()
    return [_wo_dict(w) for w in rows]


@router.get("/{wid}")
def get_work_order(
    wid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    return _wo_dict(wo)


@router.post("")
def create_work_order(
    payload: WorkOrderIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wo = WorkOrder(
        sequence_number=_next_sequence(db),
        customer_id=payload.customer_id,
        customer_reference=payload.customer_reference,
        comment=payload.comment,
        status=payload.status,
        due_date=payload.due_date,
        source_file=payload.source_file,
        external_id=payload.external_id,
        external_doc_number=payload.external_doc_number,
        custom_fields=merge_and_validate_custom_fields(
            db, "work_order", payload.custom_fields, {}, partial=False
        ),
    )
    db.add(wo)
    db.flush()
    for line in payload.lines:
        wl = WorkOrderLine(
            work_order_id=wo.id,
            product_id=line.product_id,
            free_code=line.free_code,
            description=line.description,
            quantity=line.quantity,
            unit_value=line.unit_value,
            proposed_cycle_json=line.proposed_cycle_json,
            notes=line.notes,
            line_ref=line.line_ref,
            external_id=line.external_id,
            qty_fulfilled=line.qty_fulfilled,
            custom_fields=merge_and_validate_custom_fields(
                db, "work_order_line", line.custom_fields, {}, partial=False
            ),
        )
        db.add(wl)
        db.flush()
        for comp in line.components:
            db.add(
                WorkOrderLineComponent(
                    line_id=wl.id,
                    code=comp.code,
                    description=comp.description,
                    quantity=comp.quantity,
                )
            )
    db.commit()
    db.refresh(wo)
    return _wo_dict(wo)


@router.patch("/{wid}")
def patch_work_order(
    wid: int,
    payload: WorkOrderPatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    data = payload.model_dump(exclude_unset=True)
    touched_custom = "custom_fields" in data
    custom = data.pop("custom_fields", None)
    for k, v in data.items():
        setattr(wo, k, v)
    if touched_custom:
        wo.custom_fields = merge_and_validate_custom_fields(
            db, "work_order", custom, wo.custom_fields or {}, partial=False
        )
    db.commit()
    db.refresh(wo)
    return _wo_dict(wo)


class StatusIn(BaseModel):
    status: str


@router.patch("/{wid}/status")
def patch_status(
    wid: int,
    payload: StatusIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    wo.status = payload.status
    db.commit()
    db.refresh(wo)
    return _wo_dict(wo)

@router.post("/{wid}/lines")
def add_line(
    wid: int,
    payload: LineIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    wl = WorkOrderLine(
        work_order_id=wo.id,
        product_id=payload.product_id,
        free_code=payload.free_code,
        description=payload.description,
        quantity=payload.quantity,
        unit_value=payload.unit_value,
        proposed_cycle_json=payload.proposed_cycle_json,
        notes=payload.notes,
        line_ref=payload.line_ref,
        external_id=payload.external_id,
        qty_fulfilled=payload.qty_fulfilled,
        custom_fields=merge_and_validate_custom_fields(
            db, "work_order_line", payload.custom_fields, {}, partial=False
        ),
    )
    db.add(wl)
    db.flush()
    for comp in payload.components:
        db.add(
            WorkOrderLineComponent(
                line_id=wl.id,
                code=comp.code,
                description=comp.description,
                quantity=comp.quantity,
            )
        )
    db.commit()
    db.refresh(wo)
    return _wo_dict(wo)


@router.patch("/{wid}/lines/{line_id}")
def patch_line(
    wid: int,
    line_id: int,
    payload: LinePatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wl = (
        db.query(WorkOrderLine)
        .filter_by(id=line_id, work_order_id=wid)
        .first()
    )
    if not wl:
        raise HTTPException(404, "Line not found")
    data = payload.model_dump(exclude_unset=True)
    touched_custom = "custom_fields" in data
    custom = data.pop("custom_fields", None)
    for k, v in data.items():
        setattr(wl, k, v)
    if touched_custom:
        wl.custom_fields = merge_and_validate_custom_fields(
            db, "work_order_line", custom, wl.custom_fields or {}, partial=False
        )
    db.commit()
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    return _wo_dict(wo)


@router.delete("/{wid}/lines/{line_id}")
def delete_line(
    wid: int,
    line_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wl = (
        db.query(WorkOrderLine)
        .filter_by(id=line_id, work_order_id=wid)
        .first()
    )
    if not wl:
        raise HTTPException(404, "Line not found")
    db.delete(wl)
    db.commit()
    return {"ok": True}


@router.post("/{wid}/lines/{line_id}/components")
def add_component(
    wid: int,
    line_id: int,
    payload: ComponentIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    wl = db.query(WorkOrderLine).filter_by(id=line_id, work_order_id=wid).first()
    if not wl:
        raise HTTPException(404, "Line not found")
    c = WorkOrderLineComponent(
        line_id=wl.id,
        code=payload.code,
        description=payload.description,
        quantity=payload.quantity,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return model_to_dict(c, COMP_FIELDS)


@router.patch("/{wid}/lines/{line_id}/components/{cid}")
def patch_component(
    wid: int,
    line_id: int,
    cid: int,
    payload: ComponentIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    c = (
        db.query(WorkOrderLineComponent)
        .join(WorkOrderLine)
        .filter(
            WorkOrderLineComponent.id == cid,
            WorkOrderLine.id == line_id,
            WorkOrderLine.work_order_id == wid,
        )
        .first()
    )
    if not c:
        raise HTTPException(404, "Component not found")
    c.code = payload.code
    c.description = payload.description
    c.quantity = payload.quantity
    db.commit()
    return model_to_dict(c, COMP_FIELDS)


@router.delete("/{wid}/lines/{line_id}/components/{cid}")
def delete_component(
    wid: int,
    line_id: int,
    cid: int,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    c = (
        db.query(WorkOrderLineComponent)
        .join(WorkOrderLine)
        .filter(
            WorkOrderLineComponent.id == cid,
            WorkOrderLine.id == line_id,
            WorkOrderLine.work_order_id == wid,
        )
        .first()
    )
    if not c:
        raise HTTPException(404, "Component not found")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.delete("/{wid}")
def delete_work_order(
    wid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    db.delete(wo)
    db.commit()
    return {"ok": True}


@router.post("/{wid}/generate-production-orders")
def generate_production_orders(
    wid: int,
    db: Session = Depends(get_db),
    user: User = Depends(backoffice_or_api),
):
    """Create one production order per work-order line (shop-floor executable)."""
    wo = db.query(WorkOrder).filter_by(id=wid).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    created = []
    for line in wo.lines:
        product = db.query(Product).filter_by(id=line.product_id).first() if line.product_id else None
        code = (product.code if product else None) or line.free_code or f"WO{wo.sequence_number}-{line.id}"
        order_number = f"PO-{wo.sequence_number}-{line.id}"
        if db.query(ProductionOrder).filter_by(order_number=order_number).first():
            continue
        po = ProductionOrder(
            order_number=order_number,
            customer_name=wo.customer.company_name if wo.customer else "",
            product_id=line.product_id,
            free_code=line.free_code,
            product_description=line.description,
            quantity_ordered=line.quantity,
            status=ProductionOrderStatus.todo,
            created_by=getattr(user, "id", None),
            comment=f"From work order {wo.sequence_number}",
        )
        db.add(po)
        db.flush()
        cycle = None
        if product and product.cycle_id:
            cycle = db.query(Cycle).filter_by(id=product.cycle_id).first()
        if cycle:
            for step in cycle.steps:
                db.add(
                    ProductionOrderOperation(
                        order_id=po.id,
                        operation_id=step.operation_id,
                        included=True,
                    )
                )
        db.add(
            OrderEvent(
                order_id=po.id,
                event_type=EventType.order_created,
                text=f"Created from work order {wo.sequence_number}",
                user_id=getattr(user, "id", None),
            )
        )
        created.append(po.id)
    if wo.status == "draft":
        wo.status = "confirmed"
    db.commit()
    return {"created_production_order_ids": created}
