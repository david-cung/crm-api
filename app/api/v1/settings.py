from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.setting import Setting
from app.schemas.setting import SettingResponse, SettingUpdate, SettingCreate

router = APIRouter()

@router.get("/", response_model=List[SettingResponse])
def read_settings(
    db: Session = Depends(get_db),
    category: str = None
) -> Any:
    """
    Retrieve settings.
    """
    query = db.query(Setting)
    if category:
        query = query.filter(Setting.category == category)
    return query.all()

@router.get("/by-key/{key}", response_model=SettingResponse)
def read_setting_by_key(
    key: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Get setting by key.
    """
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    *,
    db: Session = Depends(get_db),
    key: str,
    setting_in: SettingUpdate,
) -> Any:
    """
    Update a setting by key.
    """
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        # If it doesn't exist, we could create it or throw error. 
        # For settings, let's allow dynamic creation for flexible configs.
        setting = Setting(key=key, value=setting_in.value or "", category=setting_in.category or "general")
        db.add(setting)
    
    update_data = setting_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)
    
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

@router.post("/batch")
def update_batch_settings(
    *,
    db: Session = Depends(get_db),
    settings: Dict[str, str]
) -> Any:
    """
    Update multiple settings at once.
    """
    for key, value in settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
        db.add(setting)
    db.commit()
    return {"status": "ok"}
