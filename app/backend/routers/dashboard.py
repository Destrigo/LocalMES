"""Dashboard / signage read endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import InstanceStatus, Line, OperationInstance, ProductionOrder, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db)):
    """Public LAN dashboard snapshot (signage-friendly)."""
    lines = db.query(Line).filter_by(active=True).all()
    live = (
        db.query(OperationInstance)
        .filter(
            OperationInstance.status.in_(
                [InstanceStatus.in_progress, InstanceStatus.paused]
            )
        )
        .all()
    )
    by_line = {}
    for inst in live:
        by_line.setdefault(inst.line_id, []).append(
            model_to_dict(
                inst,
                [
                    "id",
                    "order_id",
                    "operation_id",
                    "line_id",
                    "operator_count",
                    "status",
                    "quantity_produced",
                    "lot_code",
                    "started_at",
                ],
            )
        )
    orders_open = (
        db.query(ProductionOrder)
        .filter(ProductionOrder.status != "completed")
        .count()
    )
    return {
        "lines": [
            {
                **model_to_dict(l, ["id", "name", "group_id", "active"]),
                "active_instances": by_line.get(l.id, []),
            }
            for l in lines
        ],
        "open_production_orders": orders_open,
        "live_instance_count": len(live),
    }
