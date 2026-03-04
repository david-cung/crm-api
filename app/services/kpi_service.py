from sqlalchemy.orm import Session
from app.models.kpi import KPIEvent, UserKPI
from datetime import datetime, timezone
from typing import Optional

class KPIService:
    @staticmethod
    def log_event(
        db: Session, 
        user_id: int, 
        event_type: str, 
        points: float, 
        reference_id: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Logs a KPI event and updates the user's total score.
        """
        # 1. Create the event log
        event = KPIEvent(
            user_id=user_id,
            event_type=event_type,
            points=points,
            reference_id=reference_id,
            description=description
        )
        db.add(event)
        
        # 2. Update or Create UserKPI
        user_kpi = db.query(UserKPI).filter(UserKPI.user_id == user_id).first()
        if not user_kpi:
            user_kpi = UserKPI(user_id=user_id, total_score=0.0)
            db.add(user_kpi)
        
        user_kpi.total_score += points
        user_kpi.last_updated = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user_kpi)
        return user_kpi

kpi_service = KPIService()
