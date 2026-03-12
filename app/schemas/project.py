from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus

class ProjectBase(BaseModel):
    title: str
    customer_name: str
    status: ProjectStatus = ProjectStatus.DRAFT
    scheduled_date: Optional[datetime] = None
    location: Optional[str] = None
    system_size_kwp: float = 0.0
    panel_count: int = 0
    inverter_type: Optional[str] = None
    total_value: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProjectItemBase(BaseModel):
    item_id: int
    required_quantity: int
    issued_quantity: int = 0

class ProjectItemCreate(ProjectItemBase):
    pass

class ProjectItemResponse(ProjectItemBase):
    id: int
    item_name: Optional[str] = None
    item_sku: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class ProjectCreate(ProjectBase):
    items: Optional[List[ProjectItemCreate]] = []

class ProjectUpdate(ProjectBase):
    title: Optional[str] = None
    customer_name: Optional[str] = None
    status: Optional[ProjectStatus] = None
    scheduled_date: Optional[datetime] = None
    location: Optional[str] = None
    system_size_kwp: Optional[float] = None
    panel_count: Optional[int] = None
    inverter_type: Optional[str] = None
    total_value: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    items: Optional[List[ProjectItemCreate]] = None

class ProjectInDBBase(ProjectBase):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class ProjectResponse(ProjectInDBBase):
    items: List[ProjectItemResponse] = []
