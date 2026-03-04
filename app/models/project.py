from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from app.db.base_class import Base
from datetime import datetime, timezone
import enum

class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

class Project(Base):
    """
    Installation Order or Project (Solar/Energy focused)
    """
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    customer_name = Column(String, index=True, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    scheduled_date = Column(DateTime, nullable=True)
    location = Column(String)  # GPS coords or address
    
    # Energy Specific Fields
    system_size_kwp = Column(Float, default=0.0)
    panel_count = Column(Integer, default=0)
    inverter_type = Column(String)
    total_value = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
