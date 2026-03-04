from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime, timezone

class KPIEvent(Base):
    """
    Log of events that trigger KPI changes
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    event_type = Column(String, nullable=False) # e.g. "PROJECT_COMPLETED", "SHIPMENT_DELAYED"
    points = Column(Float, nullable=False)
    reference_id = Column(String) # ID of the related project or shipment
    description = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserKPI(Base):
    """
    Aggregated stats for each user
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, index=True)
    total_score = Column(Float, default=0.0)
    monthly_performance = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
