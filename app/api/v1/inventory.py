from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inventory import InventoryItem
from app.schemas.inventory import InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse

router = APIRouter()

@router.get("/", response_model=List[InventoryItemResponse])
def read_inventory_items(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve inventory items.
    """
    items = db.query(InventoryItem).offset(skip).limit(limit).all()
    return items


@router.post("/", response_model=InventoryItemResponse)
def create_inventory_item(
    *,
    db: Session = Depends(get_db),
    item_in: InventoryItemCreate,
) -> Any:
    """
    Create new inventory item.
    """
    # Check duplicate SKU
    existing = db.query(InventoryItem).filter(InventoryItem.sku == item_in.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    
    item = InventoryItem(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{id}", response_model=InventoryItemResponse)
def update_inventory_item(
    *,
    db: Session = Depends(get_db),
    id: int,
    item_in: InventoryItemUpdate,
) -> Any:
    """
    Update an inventory item.
    """
    item = db.query(InventoryItem).filter(InventoryItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
        
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{id}")
def delete_inventory_item(
    *,
    db: Session = Depends(get_db),
    id: int,
) -> Any:
    """
    Delete an item.
    """
    item = db.query(InventoryItem).filter(InventoryItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
