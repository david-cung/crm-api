# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base

from app.models.user import User
from app.models.role import Role
from app.models.inventory import (
    InventoryItem, Warehouse, BinLocation, InventoryLevel, 
    StockTransaction, StockTransfer, InventoryAudit, AuditItem
)
from app.models.project import Project
from app.models.logistics import Shipment, ShipmentIncident
from app.models.kpi import KPIEvent, UserKPI
