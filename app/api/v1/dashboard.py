from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.inventory import InventoryItem
from app.models.logistics import Shipment, ShipmentStatus
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.setting_service import setting_service

router = APIRouter()

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # 1. Personnel & HR
    total_users = db.query(User).count()
    avg_salary = float(setting_service.get_value(db, "hr_avg_salary_per_employee", "3000"))
    estimated_payroll = total_users * avg_salary

    # 2. Inventory
    total_inventory = db.query(InventoryItem).count()
    total_stock_value = db.query(func.sum(InventoryItem.quantity * InventoryItem.unit_price)).scalar() or 0.0

    # 3. Projects & Revenue
    revenue = db.query(func.sum(Project.total_value)).filter(Project.status == ProjectStatus.DONE).scalar() or 0.0
    target_revenue = db.query(func.sum(Project.total_value)).filter(
        Project.status.in_([ProjectStatus.APPROVED, ProjectStatus.IN_PROGRESS, ProjectStatus.DONE])
    ).scalar() or 0.0
    pending_orders = db.query(Project).filter(Project.status.in_([ProjectStatus.APPROVED, ProjectStatus.IN_PROGRESS])).count()

    # 4. Logistics & Costs
    active_shipments = db.query(Shipment).filter(Shipment.status != ShipmentStatus.DELIVERED).count()
    shipment_costs = db.query(func.sum(Shipment.total_cost)).scalar() or 0.0
    
    # Delivery Rate Calculation
    total_delivered = db.query(Shipment).filter(Shipment.status == ShipmentStatus.DELIVERED).count()
    on_time_delivered = db.query(Shipment).filter(
        Shipment.status == ShipmentStatus.DELIVERED,
        Shipment.actual_arrival <= Shipment.estimated_arrival
    ).count()
    delivery_rate = f"{(on_time_delivered / total_delivered * 100):.1f}%" if total_delivered > 0 else "100%"

    # 5. Financials
    operating_costs = shipment_costs + estimated_payroll
    gross_profit = revenue - operating_costs

    return {
        # KPI Cards (Top Row)
        "revenue": revenue,
        "target_revenue": target_revenue,
        "operating_costs": operating_costs,
        "gross_profit": gross_profit,
        "pending_orders": pending_orders,
        "delivery_rate": delivery_rate,
        
        # Legacy/Extra stats
        "total_personnel": total_users,
        "total_inventory_sku": total_inventory,
        "total_stock_value": total_stock_value,
        "active_shipments": active_shipments,
        "payroll_budget": estimated_payroll,
        "incident_rate": "0.2%", # can be calculated from ShipmentIncident
    }
