"""Shop-floor operation instances and downtime actions."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import any_role_or_api
from database import (
    CatalogOperation,
    Downtime,
    DowntimeReason,
    EventType,
    InstanceStatus,
    Line,
    OrderEvent,
    OperationInstance,
    ProductionOrder,
    ProductionOrderStatus,
    User,
    get_db,
)
from serializers import model_to_dict

router = APIRouter(prefix="/operation-instances", tags=["shop-floor"])

INSTANCE_FIELDS = [
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
]
DOWNTIME_FIELDS = ["id", "instance_id", "reason_id", "started_at", "ended_at"]


class StartIn(BaseModel):
    order_id: int
    operation_id: int
    line_id: int
    operator_count: int = Field(ge=1)


class DowntimeIn(BaseModel):
    reason_id: int


class QuantityIn(BaseModel):
    quantity_produced: int = Field(ge=0)
    lot_code: str | None = None


class OperatorsIn(BaseModel):
    operator_count: int = Field(ge=1)


def _inst_dict(i: OperationInstance) -> dict:
    data = model_to_dict(i, INSTANCE_FIELDS)
    data["downtimes"] = [model_to_dict(d, DOWNTIME_FIELDS) for d in i.downtimes]
    return data


@router.get("")
def list_instances(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    rows = (
        db.query(OperationInstance)
        .order_by(OperationInstance.started_at.desc())
        .limit(500)
        .all()
    )
    return [_inst_dict(i) for i in rows]


@router.get("/todo")
def list_todo(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    """Orders still todo/in progress with included operations not completed."""
    orders = (
        db.query(ProductionOrder)
        .filter(
            ProductionOrder.status.in_(
                [ProductionOrderStatus.todo, ProductionOrderStatus.in_progress, ProductionOrderStatus.paused]
            )
        )
        .all()
    )
    result = []
    for o in orders:
        active_ops = [op for op in o.operations if op.included]
        completed_ops = {
            i.operation_id
            for i in o.instances
            if i.status == InstanceStatus.completed
        }
        pending = [op for op in active_ops if op.operation_id not in completed_ops]
        if pending:
            result.append(
                {
                    "order": model_to_dict(
                        o,
                        [
                            "id",
                            "order_number",
                            "customer_name",
                            "product_description",
                            "quantity_ordered",
                            "status",
                        ],
                    ),
                    "pending_operation_ids": [p.operation_id for p in pending],
                }
            )
    return result


@router.get("/{iid}")
def get_instance(
    iid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    i = db.query(OperationInstance).filter_by(id=iid).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    return _inst_dict(i)


@router.post("/start")
def start(
    payload: StartIn,
    db: Session = Depends(get_db),
    user: User = Depends(any_role_or_api),
):
    order = db.query(ProductionOrder).filter_by(id=payload.order_id).first()
    if not order:
        raise HTTPException(404, "Production order not found")
    line = db.query(Line).filter_by(id=payload.line_id, active=True).first()
    if not line:
        raise HTTPException(400, "Invalid line")
    op = db.query(CatalogOperation).filter_by(id=payload.operation_id).first()
    if not op:
        raise HTTPException(400, "Invalid operation")
    compat_ids = [l.id for l in op.compatible_lines]
    if compat_ids and payload.line_id not in compat_ids:
        raise HTTPException(400, "Line is not compatible with this operation")
    if op.line_group_id and line.group_id != op.line_group_id and not compat_ids:
        raise HTTPException(
            400,
            "Line group does not match operation (and no compatible lines configured)",
        )
    inst = OperationInstance(
        order_id=payload.order_id,
        operation_id=payload.operation_id,
        line_id=payload.line_id,
        operator_count=payload.operator_count,
        status=InstanceStatus.in_progress,
        started_by=getattr(user, "id", None) or 0,
    )
    db.add(inst)
    if order.status == ProductionOrderStatus.todo:
        order.status = ProductionOrderStatus.in_progress
    db.add(
        OrderEvent(
            order_id=order.id,
            event_type=EventType.operation_started,
            text=f"Operation {payload.operation_id} started on line {payload.line_id}",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    db.refresh(inst)
    return _inst_dict(inst)


@router.post("/{iid}/pause")
def pause(iid: int, db: Session = Depends(get_db), user: User = Depends(any_role_or_api)):
    inst = db.query(OperationInstance).filter_by(id=iid).first()
    if not inst or inst.status != InstanceStatus.in_progress:
        raise HTTPException(400, "Instance not in progress")
    inst.status = InstanceStatus.paused
    order = inst.order
    order.status = ProductionOrderStatus.paused
    db.add(
        OrderEvent(
            order_id=order.id,
            event_type=EventType.operation_paused,
            text=f"Instance {iid} paused",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    return _inst_dict(inst)


@router.post("/{iid}/resume")
def resume(iid: int, db: Session = Depends(get_db), user: User = Depends(any_role_or_api)):
    inst = db.query(OperationInstance).filter_by(id=iid).first()
    if not inst or inst.status != InstanceStatus.paused:
        raise HTTPException(400, "Instance not paused")
    inst.status = InstanceStatus.in_progress
    inst.order.status = ProductionOrderStatus.in_progress
    db.add(
        OrderEvent(
            order_id=inst.order_id,
            event_type=EventType.operation_resumed,
            text=f"Instance {iid} resumed",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    return _inst_dict(inst)


@router.post("/{iid}/downtimes")
def declare_downtime(
    iid: int,
    payload: DowntimeIn,
    db: Session = Depends(get_db),
    user: User = Depends(any_role_or_api),
):
    inst = db.query(OperationInstance).filter_by(id=iid).first()
    if not inst:
        raise HTTPException(404, "Instance not found")
    if not db.query(DowntimeReason).filter_by(id=payload.reason_id).first():
        raise HTTPException(400, "Invalid downtime reason")
    d = Downtime(instance_id=iid, reason_id=payload.reason_id)
    db.add(d)
    db.add(
        OrderEvent(
            order_id=inst.order_id,
            event_type=EventType.downtime_declared,
            text=f"Downtime declared on instance {iid}",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    db.refresh(d)
    return model_to_dict(d, DOWNTIME_FIELDS)


@router.post("/{iid}/downtimes/{did}/resolve")
def resolve_downtime(
    iid: int,
    did: int,
    db: Session = Depends(get_db),
    user: User = Depends(any_role_or_api),
):
    d = db.query(Downtime).filter_by(id=did, instance_id=iid).first()
    if not d or d.ended_at:
        raise HTTPException(400, "Open downtime not found")
    d.ended_at = datetime.utcnow()
    db.add(
        OrderEvent(
            order_id=d.instance.order_id,
            event_type=EventType.downtime_resolved,
            text=f"Downtime {did} resolved",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    return model_to_dict(d, DOWNTIME_FIELDS)


@router.post("/{iid}/complete")
def complete(
    iid: int,
    payload: QuantityIn,
    db: Session = Depends(get_db),
    user: User = Depends(any_role_or_api),
):
    inst = db.query(OperationInstance).filter_by(id=iid).first()
    if not inst or inst.status == InstanceStatus.completed:
        raise HTTPException(400, "Instance not completable")
    open_dt = [d for d in inst.downtimes if d.ended_at is None]
    for d in open_dt:
        d.ended_at = datetime.utcnow()
    inst.quantity_produced = payload.quantity_produced
    inst.lot_code = payload.lot_code
    inst.status = InstanceStatus.completed
    inst.ended_at = datetime.utcnow()
    db.add(
        OrderEvent(
            order_id=inst.order_id,
            event_type=EventType.operation_completed,
            text=f"Instance {iid} completed qty={payload.quantity_produced}",
            user_id=getattr(user, "id", None),
        )
    )
    order = inst.order
    included = [op.operation_id for op in order.operations if op.included]
    done = {
        i.operation_id
        for i in order.instances
        if i.status == InstanceStatus.completed or i.id == inst.id
    }
    if included and set(included).issubset(done):
        order.status = ProductionOrderStatus.completed
        db.add(
            OrderEvent(
                order_id=order.id,
                event_type=EventType.order_completed,
                text="All operations completed",
                user_id=getattr(user, "id", None),
            )
        )
    db.commit()
    db.refresh(inst)
    return _inst_dict(inst)


@router.patch("/{iid}/operators")
def patch_operators(
    iid: int,
    payload: OperatorsIn,
    db: Session = Depends(get_db),
    user: User = Depends(any_role_or_api),
):
    inst = db.query(OperationInstance).filter_by(id=iid).first()
    if not inst:
        raise HTTPException(404, "Instance not found")
    inst.operator_count = payload.operator_count
    db.add(
        OrderEvent(
            order_id=inst.order_id,
            event_type=EventType.operators_modified,
            text=f"Operators set to {payload.operator_count}",
            user_id=getattr(user, "id", None),
        )
    )
    db.commit()
    return _inst_dict(inst)


# Also expose downtimes as top-level list for API completeness
downtimes_router = APIRouter(prefix="/downtimes", tags=["shop-floor"])


@downtimes_router.get("")
def list_downtimes(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    return [
        model_to_dict(d, DOWNTIME_FIELDS)
        for d in db.query(Downtime).order_by(Downtime.started_at.desc()).limit(500).all()
    ]


@downtimes_router.get("/{did}")
def get_downtime(
    did: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    d = db.query(Downtime).filter_by(id=did).first()
    if not d:
        raise HTTPException(404, "Downtime not found")
    return model_to_dict(d, DOWNTIME_FIELDS)
