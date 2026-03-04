from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KPIEventBase(BaseModel):
    user_id: int
    event_type: str
    points: float
    reference_id: Optional[str] = None
    description: Optional[str] = None

class KPIEventCreate(KPIEventBase):
    pass

class KPIEventResponse(KPIEventBase):
    id: int
    timestamp: datetime
    model_config = {
        "from_attributes": True
    }

class UserKPIResponse(BaseModel):
    user_id: int
    total_score: float
    monthly_performance: float
    last_updated: datetime
    model_config = {
        "from_attributes": True
    }
