from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.procurement import POStatus


# --- Supplier ---
class SupplierBase(BaseModel):
    name: str
    code: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_code: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_code: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Purchase Order Item ---
class POItemBase(BaseModel):
    item_id: int
    quantity: int
    unit_price: float


class POItemCreate(POItemBase):
    pass


class POItemResponse(POItemBase):
    id: int
    received_quantity: int = 0
    item_name: Optional[str] = None
    item_sku: Optional[str] = None
    model_config = {"from_attributes": True}


# --- Purchase Order ---
class PurchaseOrderBase(BaseModel):
    supplier_id: int
    warehouse_id: int
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[POItemCreate]


class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    po_number: str
    status: POStatus
    total_amount: float
    created_by: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    items: List[POItemResponse] = []
    supplier_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    model_config = {"from_attributes": True}


class POStatusUpdate(BaseModel):
    status: POStatus


# --- Goods Receipt ---
class GoodsReceiptCreate(BaseModel):
    items: List[dict]  # [{"item_id": 1, "received_qty": 10}, ...]
    notes: Optional[str] = None


class GoodsReceiptResponse(BaseModel):
    id: int
    grn_number: str
    po_id: int
    warehouse_id: int
    received_by: str
    notes: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
