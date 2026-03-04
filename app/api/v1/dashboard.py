from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.inventory import InventoryItem
from app.models.logistics import Shipment
from app.models.user import User

router = APIRouter()

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_inventory = db.query(InventoryItem).count()
    total_users = db.query(User).count()
    active_shipments = db.query(Shipment).filter(Shipment.status != "DELIVERED").count()
    # Add more stats as needed
    return {
        "total_personnel": total_users,
        "total_inventory_sku": total_inventory,
        "active_shipments": active_shipments,
        "incident_rate": "0.5%", # Placeholder
    }
