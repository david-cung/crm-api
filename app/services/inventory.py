from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.inventory import (
    InventoryItem, InventoryLevel, StockTransaction, 
    TransactionType, Warehouse, BinLocation, StockTransfer
)
from app.schemas.inventory import StockTransactionCreate, StockTransferCreate
from datetime import datetime, timezone
from typing import Optional

class InventoryService:
    @staticmethod
    def get_or_create_level(db: Session, item_id: int, warehouse_id: int, bin_id: Optional[int] = None) -> InventoryLevel:
        level = db.query(InventoryLevel).filter(
            InventoryLevel.item_id == item_id,
            InventoryLevel.warehouse_id == warehouse_id,
            InventoryLevel.bin_id == bin_id
        ).first()
        
        if not level:
            level = InventoryLevel(
                item_id=item_id,
                warehouse_id=warehouse_id,
                bin_id=bin_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                quantity_on_order=0
            )
            db.add(level)
            db.commit()
            db.refresh(level)
        return level

    @staticmethod
    def create_transaction(db: Session, transaction_in: StockTransactionCreate, user_id: int) -> StockTransaction:
        # Create transaction record
        transaction = StockTransaction(
            **transaction_in.model_dump(),
            created_by_id=user_id
        )
        db.add(transaction)
        
        # Update Inventory Level
        level = InventoryService.get_or_create_level(
            db, 
            transaction_in.item_id, 
            transaction_in.warehouse_id, 
            transaction_in.bin_id
        )
        
        # Logic depends on transaction type
        if transaction_in.transaction_type == TransactionType.IN:
            level.quantity_on_hand += transaction_in.quantity
        elif transaction_in.transaction_type == TransactionType.OUT:
            level.quantity_on_hand -= transaction_in.quantity
            # Ensure we don't go below zero if business rules dictate
        elif transaction_in.transaction_type == TransactionType.ADJUSTMENT:
            level.quantity_on_hand += transaction_in.quantity
        
        db.add(level)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def initiate_transfer(db: Session, transfer_in: StockTransferCreate) -> StockTransfer:
        transfer = StockTransfer(
            **transfer_in.model_dump(),
            status="PENDING"
        )
        db.add(transfer)
        
        # Reserve stock in origin warehouse
        level_from = InventoryService.get_or_create_level(db, transfer_in.item_id, transfer_in.from_warehouse_id)
        level_from.quantity_reserved += transfer_in.quantity
        
        db.add(level_from)
        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def ship_transfer(db: Session, transfer_id: int) -> StockTransfer:
        transfer = db.query(StockTransfer).filter(StockTransfer.id == transfer_id).first()
        if not transfer:
            return None
        
        transfer.status = "IN_TRANSIT"
        transfer.shipped_at = datetime.now(timezone.utc)
        
        # Deduct from on_hand and remove from reserved at origin
        level_from = InventoryService.get_or_create_level(db, transfer.item_id, transfer.from_warehouse_id)
        level_from.quantity_on_hand -= transfer.quantity
        level_from.quantity_reserved -= transfer.quantity
        
        db.add(level_from)
        db.add(transfer)
        db.commit()
        db.refresh(transfer)
        return transfer

    @staticmethod
    def receive_transfer(db: Session, transfer_id: int) -> StockTransfer:
        transfer = db.query(StockTransfer).filter(StockTransfer.id == transfer_id).first()
        if not transfer:
            return None
        
        transfer.status = "COMPLETED"
        transfer.received_at = datetime.now(timezone.utc)
        
        # Add to on_hand at destination
        level_to = InventoryService.get_or_create_level(db, transfer.item_id, transfer.to_warehouse_id)
        level_to.quantity_on_hand += transfer.quantity
        
        db.add(level_to)
        db.add(transfer)
        db.commit()
        db.refresh(transfer)
        return transfer
