"""Customers CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_api
from custom_fields import merge_and_validate_custom_fields
from database import Customer, User, get_db
from serializers import model_to_dict

router = APIRouter(prefix="/customers", tags=["customers"])

FIELDS = [
    "id",
    "company_name",
    "customer_code",
    "vat_number",
    "email",
    "phone",
    "address",
    "notes",
    "active",
    "created_at",
    "external_id",
    "custom_fields",
]


class CustomerIn(BaseModel):
    company_name: str
    customer_code: str | None = None
    vat_number: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    active: bool = True
    external_id: str | None = None
    custom_fields: dict | None = None


class CustomerPatch(BaseModel):
    company_name: str | None = None
    customer_code: str | None = None
    vat_number: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    active: bool | None = None
    external_id: str | None = None
    custom_fields: dict | None = None


@router.get("")
def list_customers(
    q: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    query = db.query(Customer)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Customer.company_name.ilike(like))
            | (Customer.customer_code.ilike(like))
            | (Customer.vat_number.ilike(like))
        )
    query = query.order_by(Customer.company_name)
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {
        "items": [model_to_dict(c, FIELDS) for c in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{cid}")
def get_customer(
    cid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    c = db.query(Customer).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Customer not found")
    return model_to_dict(c, FIELDS)


@router.post("")
def create_customer(
    payload: CustomerIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    data = payload.model_dump()
    custom = data.pop("custom_fields", None)
    existing = None
    if payload.external_id:
        existing = db.query(Customer).filter_by(external_id=payload.external_id).first()
    if not existing and payload.customer_code:
        existing = db.query(Customer).filter_by(customer_code=payload.customer_code).first()
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        existing.custom_fields = merge_and_validate_custom_fields(
            db, "customer", custom, existing.custom_fields or {}, partial=False
        )
        db.commit()
        db.refresh(existing)
        return model_to_dict(existing, FIELDS)
    c = Customer(**data)
    c.custom_fields = merge_and_validate_custom_fields(
        db, "customer", custom, {}, partial=False
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return model_to_dict(c, FIELDS)


@router.patch("/{cid}")
def patch_customer(
    cid: int,
    payload: CustomerPatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    c = db.query(Customer).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Customer not found")
    data = payload.model_dump(exclude_unset=True)
    touched_custom = "custom_fields" in data
    custom = data.pop("custom_fields", None)
    for k, v in data.items():
        setattr(c, k, v)
    if touched_custom:
        c.custom_fields = merge_and_validate_custom_fields(
            db, "customer", custom, c.custom_fields or {}, partial=False
        )
    db.commit()
    return model_to_dict(c, FIELDS)


@router.delete("/{cid}")
def delete_customer(
    cid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    c = db.query(Customer).filter_by(id=cid).first()
    if not c:
        raise HTTPException(404, "Customer not found")
    db.delete(c)
    db.commit()
    return {"ok": True}
