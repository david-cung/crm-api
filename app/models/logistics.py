from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime, timezone
import enum

class ShipmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class Shipment(Base):
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True, nullable=False)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING, nullable=False)
    origin = Column(String)
    destination = Column(String)
    current_location = Column(String)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    total_cost = Column(Float, default=0.0)
    
    incidents = relationship("ShipmentIncident", back_populates="shipment")

class ShipmentIncident(Base):
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipment.id"), nullable=False)
    description = Column(String, nullable=False)
    incident_type = Column(String) # e.g., "Delay", "Damage", "Customs Hold"
    image_url = Column(String, nullable=True) # Linked to S3/MinIO
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    shipment = relationship("Shipment", back_populates="incidents")
