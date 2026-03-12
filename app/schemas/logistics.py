from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.logistics import ShipmentStatus, VehicleStatus, DriverStatus, TripStatus

class VehicleBase(BaseModel):
    license_plate: str
    vehicle_type: Optional[str] = None
    capacity_weight: float = 0.0
    capacity_volume: float = 0.0
    status: VehicleStatus = VehicleStatus.AVAILABLE
    notes: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(VehicleBase):
    license_plate: Optional[str] = None

class VehicleResponse(VehicleBase):
    id: int
    model_config = {"from_attributes": True}

class DriverBase(BaseModel):
    name: str
    phone: str
    license_type: Optional[str] = None
    status: DriverStatus = DriverStatus.AVAILABLE
    notes: Optional[str] = None

class DriverCreate(DriverBase):
    pass

class DriverUpdate(DriverBase):
    name: Optional[str] = None
    phone: Optional[str] = None

class DriverResponse(DriverBase):
    id: int
    model_config = {"from_attributes": True}

class ShipmentIncidentBase(BaseModel):
    description: str
    incident_type: str
    image_url: Optional[str] = None

class ShipmentIncidentCreate(ShipmentIncidentBase):
    shipment_id: int

class ShipmentIncidentResponse(ShipmentIncidentBase):
    id: int
    reported_at: datetime
    model_config = {"from_attributes": True}

class ShipmentBase(BaseModel):
    tracking_number: str
    trip_id: Optional[int] = None
    origin: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    current_location: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    total_cost: float = 0.0
    po_id: Optional[int] = None
    project_id: Optional[int] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentUpdate(ShipmentBase):
    tracking_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[ShipmentStatus] = None

class ShipmentResponse(ShipmentBase):
    id: int
    incidents: List[ShipmentIncidentResponse] = []
    model_config = {"from_attributes": True}

class TripBase(BaseModel):
    trip_number: str
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    status: TripStatus = TripStatus.DRAFT
    route_summary: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class TripCreate(TripBase):
    pass

class TripUpdate(TripBase):
    trip_number: Optional[str] = None

class TripResponse(TripBase):
    id: int
    created_at: datetime
    vehicle: Optional[VehicleResponse] = None
    driver: Optional[DriverResponse] = None
    shipments: List[ShipmentResponse] = []
    model_config = {"from_attributes": True}
