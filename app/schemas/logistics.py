from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.logistics import ShipmentStatus

class ShipmentIncidentBase(BaseModel):
    description: str
    incident_type: str
    image_url: Optional[str] = None

class ShipmentIncidentCreate(ShipmentIncidentBase):
    shipment_id: int

class ShipmentIncidentResponse(ShipmentIncidentBase):
    id: int
    reported_at: datetime
    model_config = {
        "from_attributes": True
    }

class ShipmentBase(BaseModel):
    tracking_number: str
    origin: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    current_location: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    total_cost: float = 0.0

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
    model_config = {
        "from_attributes": True
    }
