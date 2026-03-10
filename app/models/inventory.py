from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime, timezone
import enum

class TransactionType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    AUDIT = "AUDIT"

class AuditStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Warehouse(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    address = Column(String)
    is_active = Column(Boolean, default=True)
    
    bins = relationship("BinLocation", back_populates="warehouse")
    inventory_levels = relationship("InventoryLevel", back_populates="warehouse")

class BinLocation(Base):
    __tablename__ = "bin_location"
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    code = Column(String, index=True, nullable=False) # e.g. A-1-1
    description = Column(String)
    
    warehouse = relationship("Warehouse", back_populates="bins")
    inventory_levels = relationship("InventoryLevel", back_populates="bin")

class InventoryItem(Base):
    __tablename__ = "inventory_item"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    category = Column(String, index=True)
    unit = Column(String, default="unit") # pcs, kg, m, etc.
    unit_price = Column(Float, nullable=False)
    
    # Thresholds
    min_stock = Column(Integer, default=0)
    max_stock = Column(Integer, default=1000)
    reorder_point = Column(Integer, default=5)
    
    levels = relationship("InventoryLevel", back_populates="item")
    transactions = relationship("StockTransaction", back_populates="item")

class InventoryLevel(Base):
    __tablename__ = "inventory_level"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_item.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("bin_location.id"), nullable=True)
    
    quantity_on_hand = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)
    quantity_on_order = Column(Integer, default=0, nullable=False)
    
    item = relationship("InventoryItem", back_populates="levels")
    warehouse = relationship("Warehouse", back_populates="inventory_levels")
    bin = relationship("BinLocation", back_populates="inventory_levels")

    @property
    def quantity_available(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved

class StockTransaction(Base):
    __tablename__ = "stock_transaction"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_item.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("bin_location.id"), nullable=True)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False) # Positive for IN, Negative for OUT
    reference = Column(String) # PO number, SO number, etc.
    notes = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_id = Column(Integer, ForeignKey("user.id"))

    item = relationship("InventoryItem", back_populates="transactions")

class StockTransfer(Base):
    __tablename__ = "stock_transfer"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_item.id"), nullable=False)
    from_warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="PENDING") # PENDING, IN_TRANSIT, COMPLETED
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    shipped_at = Column(DateTime)
    received_at = Column(DateTime)

class InventoryAudit(Base):
    __tablename__ = "inventory_audit"
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouse.id"), nullable=False)
    status = Column(Enum(AuditStatus), default=AuditStatus.PENDING)
    audit_type = Column(String) # FULL, CYCLE
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    items = relationship("AuditItem", back_populates="audit")

class AuditItem(Base):
    __tablename__ = "audit_item"
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("inventory_audit.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_item.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("bin_location.id"))
    
    expected_quantity = Column(Integer, nullable=False)
    actual_quantity = Column(Integer)
    difference = Column(Integer)
    
    audit = relationship("InventoryAudit", back_populates="items")
