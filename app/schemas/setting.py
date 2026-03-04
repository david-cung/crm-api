from pydantic import BaseModel
from typing import Optional

class SettingBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: str = "general"

class SettingCreate(SettingBase):
    pass

class SettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class SettingResponse(SettingBase):
    id: int

    class Config:
        from_attributes = True
