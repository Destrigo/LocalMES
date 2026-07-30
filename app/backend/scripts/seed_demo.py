"""Seed demo master data for LocalMES."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (  # noqa: E402
    CatalogOperation,
    Customer,
    Cycle,
    CycleStep,
    DowntimeReason,
    Line,
    LineGroup,
    Product,
    SessionLocal,
    init_db,
)


def main():
    init_db()
    db = SessionLocal()
    try:
        if db.query(LineGroup).count() == 0:
            g = LineGroup(name="Assembly", active=True)
            db.add(g)
            db.flush()
            line = Line(name="Line 1", group_id=g.id, active=True)
            db.add(line)
            op1 = CatalogOperation(
                code="ASM", description="Assemble", line_group_id=g.id, active=True
            )
            op2 = CatalogOperation(
                code="QC", description="Quality check", line_group_id=g.id, active=True
            )
            db.add_all([op1, op2])
            db.flush()
            op1.compatible_lines = [line]
            op2.compatible_lines = [line]
            cycle = Cycle(name="Standard assembly", description="Demo cycle", active=True)
            db.add(cycle)
            db.flush()
            db.add_all(
                [
                    CycleStep(cycle_id=cycle.id, operation_id=op1.id, position=1),
                    CycleStep(cycle_id=cycle.id, operation_id=op2.id, position=2),
                ]
            )
            db.add(
                Product(
                    code="DEMO-001",
                    description="Demo widget",
                    customer_name="Demo Customer",
                    cycle_id=cycle.id,
                )
            )
            db.add(
                Customer(
                    company_name="Demo Customer",
                    customer_code="DEMO",
                    email="demo@example.com",
                    active=True,
                )
            )
            db.add(DowntimeReason(label="Material shortage", active=True))
            db.add(DowntimeReason(label="Machine fault", active=True))
            db.commit()
            print("Demo data seeded.")
        else:
            print("Database already has line groups; skip.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
