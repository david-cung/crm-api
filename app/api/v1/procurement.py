from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.models.procurement import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, POStatus
from app.models.inventory import InventoryItem, InventoryLevel, StockTransaction, Warehouse
from app.schemas.procurement import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    PurchaseOrderCreate, PurchaseOrderResponse, POStatusUpdate,
    GoodsReceiptCreate, GoodsReceiptResponse,
)

router = APIRouter()


# ==================== SUPPLIERS ====================

@router.get("/suppliers", response_model=List[SupplierResponse])
def list_suppliers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> Any:
    return db.query(Supplier).offset(skip).limit(limit).all()


@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(*, db: Session = Depends(get_db), supplier_in: SupplierCreate) -> Any:
    supplier = Supplier(**supplier_in.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(*, db: Session = Depends(get_db), supplier_id: int, supplier_in: SupplierUpdate) -> Any:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for field, value in supplier_in.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(*, db: Session = Depends(get_db), supplier_id: int) -> Any:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(supplier)
    db.commit()
    return {"detail": "Supplier deleted"}


# ==================== PURCHASE ORDERS ====================

@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(db: Session = Depends(get_db), skip: int = 0, limit: int = 50) -> Any:
    pos = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for po in pos:
        po_dict = PurchaseOrderResponse.model_validate(po).model_dump()
        po_dict["supplier_name"] = po.supplier.name if po.supplier else None
        po_dict["warehouse_name"] = po.warehouse.name if po.warehouse else None
        # Enrich items with product names
        enriched_items = []
        for item in po.items:
            item_dict = {
                "id": item.id,
                "item_id": item.item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "received_quantity": item.received_quantity,
                "item_name": item.inventory_item.name if item.inventory_item else None,
                "item_sku": item.inventory_item.sku if item.inventory_item else None,
            }
            enriched_items.append(item_dict)
        po_dict["items"] = enriched_items
        results.append(po_dict)
    return results


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)) -> Any:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    po_dict = PurchaseOrderResponse.model_validate(po).model_dump()
    po_dict["supplier_name"] = po.supplier.name if po.supplier else None
    po_dict["warehouse_name"] = po.warehouse.name if po.warehouse else None
    enriched_items = []
    for item in po.items:
        item_dict = {
            "id": item.id,
            "item_id": item.item_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "received_quantity": item.received_quantity,
            "item_name": item.inventory_item.name if item.inventory_item else None,
            "item_sku": item.inventory_item.sku if item.inventory_item else None,
        }
        enriched_items.append(item_dict)
    po_dict["items"] = enriched_items
    return po_dict


@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
def create_purchase_order(*, db: Session = Depends(get_db), po_in: PurchaseOrderCreate) -> Any:
    # Generate PO number
    po_number = f"PO-{datetime.now(timezone.utc).strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    total = sum(item.quantity * item.unit_price for item in po_in.items)

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=po_in.supplier_id,
        warehouse_id=po_in.warehouse_id,
        notes=po_in.notes,
        total_amount=total,
    )
    db.add(po)
    db.flush()  # Get PO id

    for item_data in po_in.items:
        po_item = PurchaseOrderItem(
            po_id=po.id,
            item_id=item_data.item_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
        )
        db.add(po_item)

    db.commit()
    db.refresh(po)
    return po


@router.patch("/purchase-orders/{po_id}/status", response_model=PurchaseOrderResponse)
def update_po_status(*, db: Session = Depends(get_db), po_id: int, status_in: POStatusUpdate) -> Any:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    po.status = status_in.status
    if status_in.status == POStatus.APPROVED:
        po.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(po)
    return po


# ==================== GOODS RECEIPT (the magic integration) ====================

@router.post("/purchase-orders/{po_id}/receive", response_model=GoodsReceiptResponse)
def receive_goods(*, db: Session = Depends(get_db), po_id: int, receipt_in: GoodsReceiptCreate) -> Any:
    """
    Receive goods for a PO.
    This is the CRITICAL integration point:
    1. Creates a GoodsReceipt (GRN)
    2. Updates PO item received_quantity
    3. Auto-creates StockTransaction(type=IN) for each item → updates inventory
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    if po.status not in [POStatus.APPROVED, POStatus.SENT, POStatus.PARTIALLY_RECEIVED]:
        raise HTTPException(status_code=400, detail=f"Cannot receive goods for PO in status: {po.status}")

    # Create GRN
    grn_number = f"GRN-{datetime.now(timezone.utc).strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    grn = GoodsReceipt(
        grn_number=grn_number,
        po_id=po.id,
        warehouse_id=po.warehouse_id,
        notes=receipt_in.notes,
    )
    db.add(grn)

    all_fully_received = True

    for recv_item in receipt_in.items:
        item_id = recv_item["item_id"]
        received_qty = recv_item["received_qty"]

        # Update PO item received_quantity
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.po_id == po.id,
            PurchaseOrderItem.item_id == item_id
        ).first()
        if not po_item:
            raise HTTPException(status_code=400, detail=f"Item {item_id} not found in PO")

        po_item.received_quantity += received_qty

        if po_item.received_quantity < po_item.quantity:
            all_fully_received = False

        # === AUTO-CREATE STOCK TRANSACTION (Integration with Inventory) ===
        stock_tx = StockTransaction(
            item_id=item_id,
            warehouse_id=po.warehouse_id,
            transaction_type="IN",
            quantity=received_qty,
            reference=grn_number,
            notes=f"Auto-received from PO {po.po_number}",
        )
        db.add(stock_tx)

        # Update InventoryLevel
        level = db.query(InventoryLevel).filter(
            InventoryLevel.item_id == item_id,
            InventoryLevel.warehouse_id == po.warehouse_id
        ).first()

        if level:
            level.quantity_on_hand += received_qty
        else:
            # Create new inventory level if item not yet in this warehouse
            level = InventoryLevel(
                item_id=item_id,
                warehouse_id=po.warehouse_id,
                quantity_on_hand=received_qty,
                quantity_reserved=0,
            )
            db.add(level)

    # Update PO status
    if all_fully_received:
        po.status = POStatus.COMPLETED
    else:
        po.status = POStatus.PARTIALLY_RECEIVED

    db.commit()
    db.refresh(grn)
    return grn


# ==================== STATS ====================

@router.get("/stats")
def get_procurement_stats(db: Session = Depends(get_db)) -> Any:
    total_pos = db.query(PurchaseOrder).count()
    pending_approval = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_([POStatus.DRAFT, POStatus.PENDING_APPROVAL])
    ).count()
    active_suppliers = db.query(Supplier).filter(Supplier.is_active == True).count()

    # Total value this month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_value = 0.0
    pos_this_month = db.query(PurchaseOrder).filter(PurchaseOrder.created_at >= month_start).all()
    for po in pos_this_month:
        monthly_value += po.total_amount

    return {
        "total_pos": total_pos,
        "pending_approval": pending_approval,
        "active_suppliers": active_suppliers,
        "monthly_value": monthly_value,
    }
