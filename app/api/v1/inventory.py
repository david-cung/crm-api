from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inventory import InventoryItem, Warehouse, BinLocation, StockTransaction, StockTransfer
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    WarehouseCreate, WarehouseResponse,
    BinLocationCreate, BinLocationResponse,
    StockTransactionCreate, StockTransactionResponse,
    StockTransferCreate, StockTransferResponse
)
from app.services.inventory import InventoryService

router = APIRouter()

# --- Inventory Items ---

@router.get("/items", response_model=List[InventoryItemResponse])
def read_inventory_items(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return db.query(InventoryItem).offset(skip).limit(limit).all()

@router.post("/items", response_model=InventoryItemResponse)
def create_inventory_item(
    *,
    db: Session = Depends(get_db),
    item_in: InventoryItemCreate,
) -> Any:
    existing = db.query(InventoryItem).filter(InventoryItem.sku == item_in.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    
    item = InventoryItem(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/items/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
    item_in: InventoryItemUpdate,
) -> Any:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(item, field, update_data[field])
    
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/items/{item_id}", response_model=InventoryItemResponse)
def delete_inventory_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
) -> Any:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return item

@router.get("/items/barcode/{barcode}", response_model=InventoryItemResponse)
def read_item_by_barcode(barcode: str, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.barcode == barcode).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# --- Warehouses ---

@router.post("/warehouses", response_model=WarehouseResponse)
def create_warehouse(warehouse_in: WarehouseCreate, db: Session = Depends(get_db)):
    warehouse = Warehouse(**warehouse_in.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse

@router.get("/warehouses", response_model=List[WarehouseResponse])
def read_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

# --- Stock Operations ---

@router.post("/transactions", response_model=StockTransactionResponse)
def create_transaction(
    transaction_in: StockTransactionCreate, 
    db: Session = Depends(get_db)
):
    # For now, using a dummy user_id=1. In real app, get from Depends(get_current_user)
    return InventoryService.create_transaction(db, transaction_in, user_id=1)

@router.post("/transfers", response_model=StockTransferResponse)
def initiate_transfer(transfer_in: StockTransferCreate, db: Session = Depends(get_db)):
    return InventoryService.initiate_transfer(db, transfer_in)

@router.post("/transfers/{id}/ship", response_model=StockTransferResponse)
def ship_transfer(id: int, db: Session = Depends(get_db)):
    transfer = InventoryService.ship_transfer(db, id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer

@router.post("/transfers/{id}/receive", response_model=StockTransferResponse)
def receive_transfer(id: int, db: Session = Depends(get_db)):
    transfer = InventoryService.receive_transfer(db, id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer
# --- Reports & Stats ---

@router.get("/transactions", response_model=List[StockTransactionResponse])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    return db.query(StockTransaction).order_by(StockTransaction.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/stats", response_model=Any)
def get_inventory_stats(db: Session = Depends(get_db)):
    # Summary stats for the warehouse dashboard
    items_count = db.query(InventoryItem).count()
    
    # Calculate low stock items (Available <= reorder_point)
    # This is a bit complex in pure SQL because available is computed,
    # for simplicity in this MVP we'll do it in memory or simple query if possible.
    all_items = db.query(InventoryItem).all()
    low_stock_count = 0
    for item in all_items:
        available = sum(lvl.quantity_on_hand - lvl.quantity_reserved for lvl in item.levels)
        if available <= item.reorder_point:
            low_stock_count += 1
            
    active_transfers = db.query(StockTransfer).filter(StockTransfer.status != "COMPLETED").count()
    
    return {
        "total_items": items_count,
        "low_stock_items": low_stock_count,
        "active_transfers": active_transfers,
        "total_value": sum(i.unit_price * sum(l.quantity_on_hand for l in i.levels) for i in all_items)
    }
