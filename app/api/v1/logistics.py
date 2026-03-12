from typing import Any, List
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.logistics import Shipment, ShipmentIncident, Vehicle, Driver, Trip
from app.schemas.logistics import (
    ShipmentCreate, 
    ShipmentUpdate, 
    ShipmentResponse, 
    ShipmentIncidentCreate, 
    ShipmentIncidentResponse,
    VehicleCreate, VehicleUpdate, VehicleResponse,
    DriverCreate, DriverUpdate, DriverResponse,
    TripCreate, TripUpdate, TripResponse
)
from app.core.redis import redis_client
from app.services.setting_service import setting_service
from app.services.kpi_service import kpi_service

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

# --- FLEET MANAGEMENT ---

@router.get("/vehicles", response_model=List[VehicleResponse])
def read_vehicles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return db.query(Vehicle).offset(skip).limit(limit).all()

@router.post("/vehicles", response_model=VehicleResponse)
def create_vehicle(
    *,
    db: Session = Depends(get_db),
    vehicle_in: VehicleCreate,
) -> Any:
    vehicle = Vehicle(**vehicle_in.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.patch("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    *,
    db: Session = Depends(get_db),
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
) -> Any:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    update_data = vehicle_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)
    
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.get("/drivers", response_model=List[DriverResponse])
def read_drivers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return db.query(Driver).offset(skip).limit(limit).all()

@router.post("/drivers", response_model=DriverResponse)
def create_driver(
    *,
    db: Session = Depends(get_db),
    driver_in: DriverCreate,
) -> Any:
    driver = Driver(**driver_in.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
def update_driver(
    *,
    db: Session = Depends(get_db),
    driver_id: int,
    driver_in: DriverUpdate,
) -> Any:
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    update_data = driver_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)
    
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

# --- DISPATCH MANAGEMENT ---

@router.get("/trips", response_model=List[TripResponse])
def read_trips(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return db.query(Trip).offset(skip).limit(limit).all()

@router.post("/trips", response_model=TripResponse)
def create_trip(
    *,
    db: Session = Depends(get_db),
    trip_in: TripCreate,
) -> Any:
    trip = Trip(**trip_in.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@router.patch("/trips/{trip_id}", response_model=TripResponse)
def update_trip(
    *,
    db: Session = Depends(get_db),
    trip_id: int,
    trip_in: TripUpdate,
) -> Any:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    update_data = trip_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip
