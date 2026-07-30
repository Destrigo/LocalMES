"""
SQLite connection and LocalMES schema (English identifiers).
"""

from __future__ import annotations

import os
from datetime import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("MES_DATABASE_PATH", os.path.join(BASE_DIR, "database.db"))
DATABASE_URL = os.environ.get("MES_DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

operation_lines = Table(
    "operation_lines",
    Base.metadata,
    Column("operation_id", Integer, ForeignKey("catalog_operations.id"), primary_key=True),
    Column("line_id", Integer, ForeignKey("lines.id"), primary_key=True),
)


class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    backoffice = "backoffice"
    operator = "operator"


class ProductionOrderStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    paused = "paused"
    completed = "completed"


class InstanceStatus(str, enum.Enum):
    in_progress = "in_progress"
    paused = "paused"
    completed = "completed"


class EventType(str, enum.Enum):
    order_created = "order_created"
    operation_started = "operation_started"
    operation_paused = "operation_paused"
    operation_resumed = "operation_resumed"
    downtime_declared = "downtime_declared"
    downtime_resolved = "downtime_resolved"
    operation_completed = "operation_completed"
    order_completed = "order_completed"
    order_modified = "order_modified"
    quantity_declared = "quantity_declared"
    operators_modified = "operators_modified"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SAEnum(RoleEnum), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LineGroup(Base):
    __tablename__ = "line_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    lines = relationship("Line", back_populates="group")
    catalog_operations = relationship("CatalogOperation", back_populates="line_group")


class Line(Base):
    __tablename__ = "lines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    group_id = Column(Integer, ForeignKey("line_groups.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    group = relationship("LineGroup", back_populates="lines")
    instances = relationship("OperationInstance", back_populates="line")
    compatible_operations = relationship(
        "CatalogOperation", secondary=operation_lines, back_populates="compatible_lines"
    )


class CatalogOperation(Base):
    __tablename__ = "catalog_operations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    line_group_id = Column(Integer, ForeignKey("line_groups.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    pieces_per_hour = Column(Float, nullable=True)
    line_group = relationship("LineGroup", back_populates="catalog_operations")
    cycle_steps = relationship("CycleStep", back_populates="operation")
    compatible_lines = relationship(
        "Line", secondary=operation_lines, back_populates="compatible_operations"
    )
    order_operations = relationship("ProductionOrderOperation", back_populates="operation")
    instances = relationship("OperationInstance", back_populates="operation")


class DowntimeReason(Base):
    __tablename__ = "downtime_reasons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    downtimes = relationship("Downtime", back_populates="reason")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    customer_name = Column(String, nullable=False)
    external_id = Column(String, nullable=True, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=True)
    cycle = relationship("Cycle", back_populates="products")
    production_orders = relationship("ProductionOrder", back_populates="product")


class Cycle(Base):
    __tablename__ = "cycles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    steps = relationship(
        "CycleStep", back_populates="cycle", order_by="CycleStep.position"
    )
    products = relationship("Product", back_populates="cycle")


class CycleStep(Base):
    __tablename__ = "cycle_steps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    operation_id = Column(Integer, ForeignKey("catalog_operations.id"), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    cycle = relationship("Cycle", back_populates="steps")
    operation = relationship("CatalogOperation", back_populates="cycle_steps")


class ProductionOrder(Base):
    __tablename__ = "production_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String, unique=True, nullable=False, index=True)
    customer_name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    free_code = Column(String, nullable=True)
    product_description = Column(String, nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    status = Column(
        SAEnum(ProductionOrderStatus),
        default=ProductionOrderStatus.todo,
        nullable=False,
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comment = Column(String, nullable=True)
    product = relationship("Product", back_populates="production_orders")
    creator = relationship("User")
    operations = relationship("ProductionOrderOperation", back_populates="order")
    instances = relationship("OperationInstance", back_populates="order")
    timeline = relationship(
        "OrderEvent", back_populates="order", order_by="OrderEvent.timestamp"
    )


class ProductionOrderOperation(Base):
    __tablename__ = "production_order_operations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    operation_id = Column(Integer, ForeignKey("catalog_operations.id"), nullable=False)
    included = Column(Boolean, default=True, nullable=False)
    order = relationship("ProductionOrder", back_populates="operations")
    operation = relationship("CatalogOperation", back_populates="order_operations")


class OperationInstance(Base):
    __tablename__ = "operation_instances"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    operation_id = Column(Integer, ForeignKey("catalog_operations.id"), nullable=False)
    line_id = Column(Integer, ForeignKey("lines.id"), nullable=False)
    operator_count = Column(Integer, nullable=False)
    status = Column(
        SAEnum(InstanceStatus), default=InstanceStatus.in_progress, nullable=False
    )
    started_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity_produced = Column(Integer, nullable=True)
    lot_code = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    order = relationship("ProductionOrder", back_populates="instances")
    operation = relationship("CatalogOperation", back_populates="instances")
    line = relationship("Line", back_populates="instances")
    starter = relationship("User")
    downtimes = relationship("Downtime", back_populates="instance")


class Downtime(Base):
    __tablename__ = "downtimes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("operation_instances.id"), nullable=False)
    reason_id = Column(Integer, ForeignKey("downtime_reasons.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    instance = relationship("OperationInstance", back_populates="downtimes")
    reason = relationship("DowntimeReason", back_populates="downtimes")


class OrderEvent(Base):
    __tablename__ = "order_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(SAEnum(EventType), nullable=False)
    text = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    order = relationship("ProductionOrder", back_populates="timeline")
    user = relationship("User")


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False)
    customer_code = Column(String, unique=True, nullable=True, index=True)
    vat_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    external_id = Column(String, nullable=True, index=True)
    work_orders = relationship("WorkOrder", back_populates="customer")


class WorkOrder(Base):
    """Customer work order (job) containing product lines."""

    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sequence_number = Column(Integer, unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer_reference = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(String(32), default="draft", nullable=False, index=True)
    # draft → confirmed → in_progress → completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=True)
    source_file = Column(String, nullable=True)
    external_id = Column(String, nullable=True, index=True)
    external_doc_number = Column(String, nullable=True)
    customer = relationship("Customer", back_populates="work_orders")
    lines = relationship(
        "WorkOrderLine", back_populates="work_order", cascade="all, delete-orphan"
    )


class WorkOrderLine(Base):
    __tablename__ = "work_order_lines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    free_code = Column(String, nullable=True)
    description = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_value = Column(String, nullable=True)
    proposed_cycle_json = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    line_ref = Column(String, nullable=True)
    external_id = Column(String, nullable=True, index=True)
    qty_fulfilled = Column(Integer, nullable=True)
    work_order = relationship("WorkOrder", back_populates="lines")
    product = relationship("Product")
    components = relationship(
        "WorkOrderLineComponent", back_populates="line", cascade="all, delete-orphan"
    )


class WorkOrderLineComponent(Base):
    __tablename__ = "work_order_line_components"
    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("work_order_lines.id"), nullable=False)
    code = Column(String, nullable=True)
    description = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    line = relationship("WorkOrderLine", back_populates="components")


class Bom(Base):
    __tablename__ = "boms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_code = Column(String, nullable=False, index=True)
    parent_description = Column(String, nullable=True)
    component_code = Column(String, nullable=False)
    component_description = Column(String, nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    cost = Column(Float, nullable=True)


class BackupLog(Base):
    __tablename__ = "backup_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    path = Column(String, nullable=True)
    result = Column(String, nullable=False)  # ok | error
    message = Column(Text, nullable=True)


class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    role = Column(SAEnum(RoleEnum), nullable=False, default=RoleEnum.backoffice)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and seed default admin user."""
    import bcrypt

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(username="admin").first():
            pwd = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
            db.add(
                User(
                    username="admin",
                    password_hash=pwd,
                    role=RoleEnum.superadmin,
                    active=True,
                    must_change_password=True,
                )
            )
            db.commit()
        if not db.query(Setting).filter_by(key="backup_dir").first():
            default_backup = os.environ.get("MES_BACKUP_DIR", "")
            db.add(Setting(key="backup_dir", value=default_backup))
            db.commit()
    finally:
        db.close()
