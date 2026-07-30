"""Master data: line groups, lines, catalog operations, downtime reasons, products."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import any_role_or_api, backoffice_or_above, backoffice_or_api, superadmin_only
from custom_fields import merge_and_validate_custom_fields
from database import (
    CatalogOperation,
    DowntimeReason,
    Line,
    LineGroup,
    Product,
    User,
    get_db,
)
from serializers import model_to_dict

router = APIRouter(tags=["master-data"])

LINE_GROUP_FIELDS = ["id", "name", "active"]
LINE_FIELDS = ["id", "name", "group_id", "active"]
OP_FIELDS = [
    "id",
    "code",
    "description",
    "line_group_id",
    "active",
    "pieces_per_hour",
]
REASON_FIELDS = ["id", "label", "active"]
PRODUCT_FIELDS = [
    "id",
    "code",
    "description",
    "customer_name",
    "external_id",
    "cycle_id",
    "custom_fields",
]


# ── Line groups ──────────────────────────────────────────────────

class LineGroupIn(BaseModel):
    name: str
    active: bool = True


class LineGroupPatch(BaseModel):
    name: str | None = None
    active: bool | None = None


@router.get("/line-groups")
def list_line_groups(
    db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    return [model_to_dict(g, LINE_GROUP_FIELDS) for g in db.query(LineGroup).all()]


@router.get("/line-groups/{gid}")
def get_line_group(
    gid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    g = db.query(LineGroup).filter_by(id=gid).first()
    if not g:
        raise HTTPException(404, "Line group not found")
    return model_to_dict(g, LINE_GROUP_FIELDS)


@router.post("/line-groups")
def create_line_group(
    payload: LineGroupIn,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    g = LineGroup(name=payload.name, active=payload.active)
    db.add(g)
    db.commit()
    db.refresh(g)
    return model_to_dict(g, LINE_GROUP_FIELDS)


@router.patch("/line-groups/{gid}")
def patch_line_group(
    gid: int,
    payload: LineGroupPatch,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    g = db.query(LineGroup).filter_by(id=gid).first()
    if not g:
        raise HTTPException(404, "Line group not found")
    if payload.name is not None:
        g.name = payload.name
    if payload.active is not None:
        g.active = payload.active
    db.commit()
    return model_to_dict(g, LINE_GROUP_FIELDS)


@router.delete("/line-groups/{gid}")
def delete_line_group(
    gid: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    g = db.query(LineGroup).filter_by(id=gid).first()
    if not g:
        raise HTTPException(404, "Line group not found")
    db.delete(g)
    db.commit()
    return {"ok": True}


# ── Lines ────────────────────────────────────────────────────────

class LineIn(BaseModel):
    name: str
    group_id: int
    active: bool = True


class LinePatch(BaseModel):
    name: str | None = None
    group_id: int | None = None
    active: bool | None = None


@router.get("/lines")
def list_lines(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    return [model_to_dict(x, LINE_FIELDS) for x in db.query(Line).all()]


@router.get("/lines/{lid}")
def get_line(lid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    x = db.query(Line).filter_by(id=lid).first()
    if not x:
        raise HTTPException(404, "Line not found")
    return model_to_dict(x, LINE_FIELDS)


@router.post("/lines")
def create_line(
    payload: LineIn, db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)
):
    x = Line(name=payload.name, group_id=payload.group_id, active=payload.active)
    db.add(x)
    db.commit()
    db.refresh(x)
    return model_to_dict(x, LINE_FIELDS)


@router.patch("/lines/{lid}")
def patch_line(
    lid: int,
    payload: LinePatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_above),
):
    x = db.query(Line).filter_by(id=lid).first()
    if not x:
        raise HTTPException(404, "Line not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(x, k, v)
    db.commit()
    return model_to_dict(x, LINE_FIELDS)


@router.delete("/lines/{lid}")
def delete_line(
    lid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)
):
    x = db.query(Line).filter_by(id=lid).first()
    if not x:
        raise HTTPException(404, "Line not found")
    db.delete(x)
    db.commit()
    return {"ok": True}


# ── Catalog operations ───────────────────────────────────────────

class OperationIn(BaseModel):
    code: str
    description: str
    line_group_id: int
    active: bool = True
    pieces_per_hour: float | None = None
    compatible_line_ids: list[int] = []


class OperationPatch(BaseModel):
    code: str | None = None
    description: str | None = None
    line_group_id: int | None = None
    active: bool | None = None
    pieces_per_hour: float | None = None
    compatible_line_ids: list[int] | None = None


def _op_dict(op: CatalogOperation) -> dict:
    data = model_to_dict(op, OP_FIELDS)
    data["compatible_line_ids"] = [l.id for l in op.compatible_lines]
    return data


@router.get("/operations")
def list_operations(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    return [_op_dict(o) for o in db.query(CatalogOperation).all()]


@router.get("/operations/{oid}")
def get_operation(
    oid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    o = db.query(CatalogOperation).filter_by(id=oid).first()
    if not o:
        raise HTTPException(404, "Operation not found")
    return _op_dict(o)


@router.post("/operations")
def create_operation(
    payload: OperationIn,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_above),
):
    o = CatalogOperation(
        code=payload.code,
        description=payload.description,
        line_group_id=payload.line_group_id,
        active=payload.active,
        pieces_per_hour=payload.pieces_per_hour,
    )
    if payload.compatible_line_ids:
        o.compatible_lines = (
            db.query(Line).filter(Line.id.in_(payload.compatible_line_ids)).all()
        )
    db.add(o)
    db.commit()
    db.refresh(o)
    return _op_dict(o)


@router.patch("/operations/{oid}")
def patch_operation(
    oid: int,
    payload: OperationPatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_above),
):
    o = db.query(CatalogOperation).filter_by(id=oid).first()
    if not o:
        raise HTTPException(404, "Operation not found")
    data = payload.model_dump(exclude_unset=True)
    line_ids = data.pop("compatible_line_ids", None)
    for k, v in data.items():
        setattr(o, k, v)
    if line_ids is not None:
        o.compatible_lines = db.query(Line).filter(Line.id.in_(line_ids)).all()
    db.commit()
    db.refresh(o)
    return _op_dict(o)


@router.delete("/operations/{oid}")
def delete_operation(
    oid: int, db: Session = Depends(get_db), _: User = Depends(backoffice_or_above)
):
    o = db.query(CatalogOperation).filter_by(id=oid).first()
    if not o:
        raise HTTPException(404, "Operation not found")
    db.delete(o)
    db.commit()
    return {"ok": True}


# ── Downtime reasons ─────────────────────────────────────────────

class ReasonIn(BaseModel):
    label: str
    active: bool = True


class ReasonPatch(BaseModel):
    label: str | None = None
    active: bool | None = None


@router.get("/downtime-reasons")
def list_reasons(db: Session = Depends(get_db), _: User = Depends(any_role_or_api)):
    return [model_to_dict(r, REASON_FIELDS) for r in db.query(DowntimeReason).all()]


@router.get("/downtime-reasons/{rid}")
def get_reason(
    rid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    r = db.query(DowntimeReason).filter_by(id=rid).first()
    if not r:
        raise HTTPException(404, "Downtime reason not found")
    return model_to_dict(r, REASON_FIELDS)


@router.post("/downtime-reasons")
def create_reason(
    payload: ReasonIn, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    r = DowntimeReason(label=payload.label, active=payload.active)
    db.add(r)
    db.commit()
    db.refresh(r)
    return model_to_dict(r, REASON_FIELDS)


@router.patch("/downtime-reasons/{rid}")
def patch_reason(
    rid: int,
    payload: ReasonPatch,
    db: Session = Depends(get_db),
    _: User = Depends(superadmin_only),
):
    r = db.query(DowntimeReason).filter_by(id=rid).first()
    if not r:
        raise HTTPException(404, "Downtime reason not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    db.commit()
    return model_to_dict(r, REASON_FIELDS)


@router.delete("/downtime-reasons/{rid}")
def delete_reason(
    rid: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    r = db.query(DowntimeReason).filter_by(id=rid).first()
    if not r:
        raise HTTPException(404, "Downtime reason not found")
    db.delete(r)
    db.commit()
    return {"ok": True}


# ── Products ─────────────────────────────────────────────────────

class ProductIn(BaseModel):
    code: str
    description: str
    customer_name: str
    external_id: str | None = None
    cycle_id: int | None = None
    custom_fields: dict | None = None


class ProductPatch(BaseModel):
    code: str | None = None
    description: str | None = None
    customer_name: str | None = None
    external_id: str | None = None
    cycle_id: int | None = None
    custom_fields: dict | None = None


@router.get("/products")
def list_products(
    q: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(any_role_or_api),
):
    query = db.query(Product)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Product.code.ilike(like))
            | (Product.description.ilike(like))
            | (Product.customer_name.ilike(like))
        )
    query = query.order_by(Product.code)
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {
        "items": [model_to_dict(p, PRODUCT_FIELDS) for p in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/products/{pid}")
def get_product(
    pid: int, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    p = db.query(Product).filter_by(id=pid).first()
    if not p:
        raise HTTPException(404, "Product not found")
    return model_to_dict(p, PRODUCT_FIELDS)


@router.get("/products/by-code/{code}")
def get_product_by_code(
    code: str, db: Session = Depends(get_db), _: User = Depends(any_role_or_api)
):
    p = db.query(Product).filter_by(code=code).first()
    if not p:
        raise HTTPException(404, "Product not found")
    return model_to_dict(p, PRODUCT_FIELDS)


@router.post("/products")
def create_product(
    payload: ProductIn, db: Session = Depends(get_db), _: User = Depends(backoffice_or_api)
):
    data = payload.model_dump()
    custom = data.pop("custom_fields", None)
    existing = None
    if payload.external_id:
        existing = db.query(Product).filter_by(external_id=payload.external_id).first()
    if not existing:
        existing = db.query(Product).filter_by(code=payload.code).first()
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        existing.custom_fields = merge_and_validate_custom_fields(
            db, "product", custom, existing.custom_fields or {}, partial=False
        )
        db.commit()
        db.refresh(existing)
        return model_to_dict(existing, PRODUCT_FIELDS)
    p = Product(**data)
    p.custom_fields = merge_and_validate_custom_fields(
        db, "product", custom, {}, partial=False
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return model_to_dict(p, PRODUCT_FIELDS)


@router.patch("/products/{pid}")
def patch_product(
    pid: int,
    payload: ProductPatch,
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    p = db.query(Product).filter_by(id=pid).first()
    if not p:
        raise HTTPException(404, "Product not found")
    data = payload.model_dump(exclude_unset=True)
    touched_custom = "custom_fields" in data
    custom = data.pop("custom_fields", None)
    for k, v in data.items():
        setattr(p, k, v)
    if touched_custom:
        p.custom_fields = merge_and_validate_custom_fields(
            db, "product", custom, p.custom_fields or {}, partial=False
        )
    db.commit()
    return model_to_dict(p, PRODUCT_FIELDS)


@router.delete("/products/{pid}")
def delete_product(
    pid: int, db: Session = Depends(get_db), _: User = Depends(superadmin_only)
):
    p = db.query(Product).filter_by(id=pid).first()
    if not p:
        raise HTTPException(404, "Product not found")
    db.delete(p)
    db.commit()
    return {"ok": True}
