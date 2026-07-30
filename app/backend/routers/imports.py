"""Import endpoints for customers, products, BOMs, production orders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth import backoffice_or_api
from database import Bom, Customer, Product, ProductionOrder, ProductionOrderStatus, User, get_db
from io_utils import parse_tabular

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/customers")
async def import_customers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    rows = await parse_tabular(file)
    created = updated = skipped = 0
    warnings: list[str] = []
    for i, row in enumerate(rows, start=2):
        name = row.get("company_name") or row.get("ragione_sociale") or ""
        if not name:
            skipped += 1
            warnings.append(f"row {i}: missing company_name")
            continue
        external_id = row.get("external_id") or None
        code = row.get("customer_code") or None
        existing = None
        if external_id:
            existing = db.query(Customer).filter_by(external_id=external_id).first()
        if not existing and code:
            existing = db.query(Customer).filter_by(customer_code=code).first()
        payload = {
            "company_name": name,
            "customer_code": code,
            "vat_number": row.get("vat_number") or None,
            "email": row.get("email") or None,
            "phone": row.get("phone") or None,
            "address": row.get("address") or None,
            "notes": row.get("notes") or None,
            "external_id": external_id,
            "active": (row.get("active") or "true").lower() not in {"0", "false", "no"},
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(Customer(**payload))
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "warnings": warnings}


@router.post("/products")
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    rows = await parse_tabular(file)
    created = updated = skipped = 0
    warnings: list[str] = []
    for i, row in enumerate(rows, start=2):
        code = row.get("code") or row.get("product_code") or row.get("codice") or ""
        if not code:
            skipped += 1
            warnings.append(f"row {i}: missing code")
            continue
        external_id = row.get("external_id") or None
        existing = None
        if external_id:
            existing = db.query(Product).filter_by(external_id=external_id).first()
        if not existing:
            existing = db.query(Product).filter_by(code=code).first()
        cycle_raw = row.get("cycle_id") or ""
        cycle_id = int(cycle_raw) if cycle_raw.isdigit() else None
        payload = {
            "code": code,
            "description": row.get("description") or row.get("descrizione") or code,
            "customer_name": row.get("customer_name") or row.get("cliente") or "",
            "external_id": external_id,
            "cycle_id": cycle_id,
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(Product(**payload))
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "warnings": warnings}


@router.post("/boms")
async def import_boms(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(backoffice_or_api),
):
    rows = await parse_tabular(file)
    created = 0
    skipped = 0
    for i, row in enumerate(rows, start=2):
        parent = row.get("parent_code") or row.get("cod_padre") or ""
        component = row.get("component_code") or row.get("cod_componente") or ""
        if not parent or not component:
            skipped += 1
            continue
        qty_raw = (row.get("quantity") or row.get("quantita") or "1").replace(",", ".")
        try:
            qty = float(qty_raw)
        except ValueError:
            qty = 1.0
        cost_raw = row.get("cost") or row.get("costo") or ""
        cost = float(cost_raw.replace(",", ".")) if cost_raw else None
        db.add(
            Bom(
                parent_code=parent,
                parent_description=row.get("parent_description") or row.get("desc_padre"),
                component_code=component,
                component_description=row.get("component_description") or row.get("desc_componente"),
                quantity=qty,
                cost=cost,
            )
        )
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}


@router.post("/production-orders")
async def import_production_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(backoffice_or_api),
):
    rows = await parse_tabular(file)
    created = skipped = 0
    warnings: list[str] = []
    for i, row in enumerate(rows, start=2):
        order_number = row.get("order_number") or row.get("numero_ordine") or ""
        if not order_number:
            skipped += 1
            warnings.append(f"row {i}: missing order_number")
            continue
        if db.query(ProductionOrder).filter_by(order_number=order_number).first():
            skipped += 1
            warnings.append(f"row {i}: duplicate order_number")
            continue
        product_code = row.get("product_code") or row.get("codice_prodotto") or ""
        product = db.query(Product).filter_by(code=product_code).first() if product_code else None
        qty_raw = row.get("quantity_ordered") or row.get("quantita") or "0"
        try:
            qty = int(float(qty_raw))
        except ValueError:
            skipped += 1
            warnings.append(f"row {i}: invalid quantity")
            continue
        if qty <= 0:
            skipped += 1
            continue
        db.add(
            ProductionOrder(
                order_number=order_number,
                customer_name=(product.customer_name if product else row.get("customer_name") or ""),
                product_id=product.id if product else None,
                free_code=None if product else product_code or None,
                product_description=(
                    product.description if product else row.get("description") or product_code or order_number
                ),
                quantity_ordered=qty,
                status=ProductionOrderStatus.todo,
                created_by=getattr(user, "id", None),
                comment=row.get("comment") or None,
            )
        )
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "warnings": warnings}
