from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.kpi import KPIEvent, UserKPI
from app.schemas.kpi import KPIEventResponse, UserKPIResponse

router = APIRouter()

@router.get("/leaderboard", response_model=List[UserKPIResponse])
def get_leaderboard(
    db: Session = Depends(get_db),
    limit: int = 10,
) -> Any:
    return db.query(UserKPI).order_by(UserKPI.total_score.desc()).limit(limit).all()

@router.get("/events", response_model=List[KPIEventResponse])
def get_all_events(
    db: Session = Depends(get_db),
    limit: int = 50,
) -> Any:
    return db.query(KPIEvent).order_by(KPIEvent.timestamp.desc()).limit(limit).all()

@router.get("/events/{user_id}", response_model=List[KPIEventResponse])
def get_user_events(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    return db.query(KPIEvent).filter(KPIEvent.user_id == user_id).order_by(KPIEvent.timestamp.desc()).all()
