"""Production orders (executable shop-floor orders)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_api
from database import (
    EventType,
    OrderEvent,
    ProductionOrder,
    ProductionOrderOperation,
    ProductionOrderStatus,
    User,
    get_db,
)
from serializers import model_to_dict

router = APIRouter(prefix="/production-orders", tags=["production-orders"])

ORDER_FIELDS = [
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
]
OP_FIELDS = ["id", "order_id", "operation_id", "included"]
EVENT_FIELDS = ["id", "order_id", "timestamp", "event_type", "text", "user_id", "metadata_json"]


class OrderIn(BaseModel):
    order_number: str
    customer_name: str
    product_id: int | None = None
    free_code: str | None = None
    product_description: str
    quantity_ordered: int
    comment: str | None = None
    operation_ids: list[int] = []


class OrderPatch(BaseModel):
    customer_name: str | None = None
    product_id: int | None = None
    free_code: str | None = None
    product_description: str | None = None
    quantity_ordered: int | None = None
    status: ProductionOrderStatus | None = None
    comment: str | None = None


class IncludedPatch(BaseModel):
    included: bool


def _order_dict(o: ProductionOrder, include_ops: bool = True, include_events: bool = False) -> dict:
    data = model_to_dict(o, ORDER_FIELDS)
    if include_ops:
        data["operations"] = [model_to_dict(op, OP_FIELDS) for op in o.operations]
    if include_events:
        data["timeline"] = [model_to_dict(e, EVENT_FIELDS) for e in o.timeline]
    return data


@router.get("")
def list_orders(
    status: ProductionOrderStatus | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    q = db.query(ProductionOrder)
    if status:
        q = q.filter_by(status=status)
    rows = q.order_by(ProductionOrder.created_at.desc()).offset(offset).limit(limit).all()
    return [_order_dict(o) for o in rows]


@router.get("/{oid}")
def get_order(
    oid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    o = db.query(ProductionOrder).filter_by(id=oid).first()
    if not o:
        raise HTTPException(404, "Production order not found")
    return _order_dict(o, include_events=True)


@router.post("")
def create_order(
    payload: OrderIn,
    db: Session = Depends(get_db),
    user: User = Depends(backoffice_or_api),
):
    if db.query(ProductionOrder).filter_by(order_number=payload.order_number).first():
        raise HTTPException(400, "order_number already exists")
    o = ProductionOrder(
        order_number=payload.order_number,
        customer_name=payload.customer_name,
        product_id=payload.product_id,
        free_code=payload.free_code,
        product_description=payload.product_description,
        quantity_ordered=payload.quantity_ordered,
        comment=payload.comment,
        status=ProductionOrderStatus.todo,
        created_by=getattr(user, "id", None),
    )
    db.add(o)
    db.flush()
    for op_id in payload.operation_ids:
        db.add(
            ProductionOrderOperation(
                order_id=o.id, operation_id=op_id, included=True
            )
        )
    db.add(
        OrderEvent(
            order_id=o.id,
            event_type=EventType.order_created,
            text="Production order created",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    db.refresh(o)
    return _order_dict(o, include_events=True)


@router.patch("/{oid}")
def patch_order(
    oid: int,
    payload: OrderPatch,
    db: Session = Depends(get_db),
    user: User = Depends(backoffice_or_api),
):
    o = db.query(ProductionOrder).filter_by(id=oid).first()
    if not o:
        raise HTTPException(404, "Production order not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(o, k, v)
    db.add(
        OrderEvent(
            order_id=o.id,
            event_type=EventType.order_modified,
            text="Production order updated",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    db.refresh(o)
    return _order_dict(o, include_events=True)


@router.patch("/{oid}/operations/{op_row_id}")
def patch_included(
    oid: int,
    op_row_id: int,
    payload: IncludedPatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    row = (
        db.query(ProductionOrderOperation)
        .filter_by(id=op_row_id, order_id=oid)
        .first()
    )
    if not row:
        raise HTTPException(404, "Order operation not found")
    row.included = payload.included
    db.commit()
    return model_to_dict(row, OP_FIELDS)


@router.delete("/{oid}")
def delete_order(
    oid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    o = db.query(ProductionOrder).filter_by(id=oid).first()
    if not o:
        raise HTTPException(404, "Production order not found")
    db.delete(o)
    db.commit()
    return {"ok": True}
