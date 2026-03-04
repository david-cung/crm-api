from sqlalchemy.orm import Session
from app.models.setting import Setting
from typing import Any, Optional

class SettingService:
    @staticmethod
    def get_value(db: Session, key: str, default: Any = None) -> Any:
        """
        Retrieves a setting value by key.
        """
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            return setting.value
        return default

    @staticmethod
    def get_int(db: Session, key: str, default: int = 0) -> int:
        value = SettingService.get_value(db, key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                return default
        return default

setting_service = SettingService()
