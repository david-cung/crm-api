from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.inventory import TransactionType, AuditStatus

# Warehouse Schemas
class WarehouseBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    is_active: bool = True

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseResponse(WarehouseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# BinLocation Schemas
class BinLocationBase(BaseModel):
    warehouse_id: int
    code: str
    description: Optional[str] = None

class BinLocationCreate(BinLocationBase):
    pass

class BinLocationResponse(BinLocationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# InventoryItem Schemas
class InventoryItemBase(BaseModel):
    sku: str
    barcode: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: str = "unit"
    unit_price: float
    min_stock: int = 0
    max_stock: int = 1000
    reorder_point: int = 5

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    sku: Optional[str] = None
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    reorder_point: Optional[int] = None

class InventoryLevelResponse(BaseModel):
    warehouse_id: int
    bin_id: Optional[int] = None
    quantity_on_hand: int
    quantity_reserved: int
    quantity_on_order: int
    quantity_available: int
    model_config = ConfigDict(from_attributes=True)

class InventoryItemResponse(InventoryItemBase):
    id: int
    levels: List[InventoryLevelResponse] = []
    model_config = ConfigDict(from_attributes=True)

# StockTransaction Schemas
class StockTransactionBase(BaseModel):
    item_id: int
    warehouse_id: int
    bin_id: Optional[int] = None
    transaction_type: TransactionType
    quantity: int
    reference: Optional[str] = None
    notes: Optional[str] = None

class StockTransactionCreate(StockTransactionBase):
    pass

class StockTransactionResponse(StockTransactionBase):
    id: int
    created_at: datetime
    created_by_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# StockTransfer Schemas
class StockTransferCreate(BaseModel):
    item_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int

class StockTransferResponse(BaseModel):
    id: int
    item_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int
    status: str
    created_at: datetime
    shipped_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
