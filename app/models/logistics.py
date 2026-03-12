from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime, timezone
import enum

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"

class DriverStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    OFF_DUTY = "OFF_DUTY"

class TripStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ShipmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class Vehicle(Base):
    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String, unique=True, index=True, nullable=False)
    vehicle_type = Column(String) # e.g., "Van 1T", "Truck 5T"
    capacity_weight = Column(Float, default=0.0) # in kg
    capacity_volume = Column(Float, default=0.0) # in m3
    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False)
    notes = Column(String, nullable=True)

class Driver(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    license_type = Column(String) # e.g., "B2", "C"
    status = Column(Enum(DriverStatus), default=DriverStatus.AVAILABLE, nullable=False)
    notes = Column(String, nullable=True)

class Trip(Base):
    id = Column(Integer, primary_key=True, index=True)
    trip_number = Column(String, unique=True, index=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("driver.id"), nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.DRAFT, nullable=False)
    route_summary = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vehicle = relationship("Vehicle")
    driver = relationship("Driver")
    shipments = relationship("Shipment", back_populates="trip")

class Shipment(Base):
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True, nullable=False)
    trip_id = Column(Integer, ForeignKey("trip.id"), nullable=True)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING, nullable=False)
    origin = Column(String)
    destination = Column(String)
    current_location = Column(String)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    total_cost = Column(Float, default=0.0)
    
    # Links to other modules
    po_id = Column(Integer, ForeignKey("purchaseorder.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="shipments")
    purchase_order = relationship("PurchaseOrder")
    project = relationship("Project")
    incidents = relationship("ShipmentIncident", back_populates="shipment")

class ShipmentIncident(Base):
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipment.id"), nullable=False)
    description = Column(String, nullable=False)
    incident_type = Column(String) # e.g., "Delay", "Damage", "Customs Hold"
    image_url = Column(String, nullable=True)
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    shipment = relationship("Shipment", back_populates="incidents")
