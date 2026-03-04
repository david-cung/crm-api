from pydantic import BaseModel
from typing import Optional

class InventoryItemBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    quantity: int = 0
    min_quantity: int = 5
    unit_price: float
    category: Optional[str] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(InventoryItemBase):
    sku: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None

class InventoryItemInDBBase(InventoryItemBase):
    id: int

    model_config = {
        "from_attributes": True
    }

class InventoryItemResponse(InventoryItemInDBBase):
    pass
