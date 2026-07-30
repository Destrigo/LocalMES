"""Customers CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_api
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


@router.get("")
def list_customers(
    q: str | None = Query(None),
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
    return [model_to_dict(c, FIELDS) for c in query.order_by(Customer.company_name).all()]


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
    payload: CustomerIn, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    c = Customer(**payload.model_dump())
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
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
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
