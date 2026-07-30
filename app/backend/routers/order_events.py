"""Order timeline events API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import any_role_or_api
from database import OrderEvent, User, get_db
from pagination import paginated_dicts
from serializers import model_to_dict

router = APIRouter(prefix="/order-events", tags=["order-events"])

FIELDS = ["id", "order_id", "timestamp", "event_type", "text", "user_id", "metadata_json"]


@router.get("")
def list_events(
    order_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    q = db.query(OrderEvent).order_by(OrderEvent.timestamp.desc())
    if order_id is not None:
        q = q.filter_by(order_id=order_id)
    return paginated_dicts(q, limit, offset, lambda e: model_to_dict(e, FIELDS))


@router.get("/{eid}")
def get_event(eid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    e = db.query(OrderEvent).filter_by(id=eid).first()
    if not e:
        raise HTTPException(404, "Event not found")
    return model_to_dict(e, FIELDS)
