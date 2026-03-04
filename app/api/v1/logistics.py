from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.logistics import Shipment, ShipmentIncident
from app.schemas.logistics import (
    ShipmentCreate, 
    ShipmentUpdate, 
    ShipmentResponse, 
    ShipmentIncidentCreate, 
    ShipmentIncidentResponse
)
from app.core.redis import redis_client
from app.services.setting_service import setting_service

CACHE_KEY_PREFIX = "shipment:"
CACHE_EXPIRE = 3600  # 1 hour

router = APIRouter()

@router.get("/", response_model=List[ShipmentResponse])
def read_shipments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    # Try to get from cache for the list (optional, but let's cache individual ones)
    return db.query(Shipment).offset(skip).limit(limit).all()

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def read_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
) -> Any:
    cache_key = f"{CACHE_KEY_PREFIX}{shipment_id}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        try:
            return json.loads(cached_data)
        except Exception:
            pass

    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Cache the result
    # We need to manually serialize if we want to store it in Redis
    # Or use pydantic's model_dump_json
    response_data = ShipmentResponse.model_validate(shipment).model_dump_json()
    redis_client.setex(cache_key, CACHE_EXPIRE, response_data)
    
    return shipment

@router.post("/", response_model=ShipmentResponse)
def create_shipment(
    *,
    db: Session = Depends(get_db),
    shipment_in: ShipmentCreate,
) -> Any:
    shipment = Shipment(**shipment_in.model_dump())
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    # No need to invalidate list cache if we don't cache the list, 
    # but could invalidate if we did.
    return shipment

@router.patch("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(
    *,
    db: Session = Depends(get_db),
    shipment_id: int,
    shipment_in: ShipmentUpdate,
) -> Any:
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    update_data = shipment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shipment, field, value)
    
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    
    # KPI Trigger: If status changed to DELIVERED, award points
    if "status" in update_data and update_data["status"] == "DELIVERED":
        shipment_points = float(setting_service.get_int(db, "kpi_shipment_delivered_points", 50))
        kpi_service.log_event(
            db=db,
            user_id=1, # Placeholder
            event_type="SHIPMENT_DELIVERED",
            points=shipment_points,
            reference_id=str(shipment.id),
            description=f"Successfully delivered shipment: {shipment.tracking_number}"
        )
    
    # Invalidate cache
    redis_client.delete(f"{CACHE_KEY_PREFIX}{shipment_id}")
    
    return shipment

@router.post("/incidents", response_model=ShipmentIncidentResponse)
def report_incident(
    *,
    db: Session = Depends(get_db),
    incident_in: ShipmentIncidentCreate,
) -> Any:
    incident = ShipmentIncident(**incident_in.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    # Invalidate shipment cache since incident is linked
    redis_client.delete(f"{CACHE_KEY_PREFIX}{incident.shipment_id}")
    
    return incident
