from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime, timezone
import enum

class UserType(str, enum.Enum):
    WEB_ADMIN = "WEB_ADMIN"
    MOBILE_APP = "MOBILE_APP"

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("role.id"))
    
    # HR Fields
    phone_number = Column(String, nullable=False) # Mandatory
    user_type = Column(Enum(UserType), default=UserType.MOBILE_APP, nullable=False)
    department = Column(String, index=True, nullable=True)
    position = Column(String, nullable=True)
    join_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    avatar_url = Column(String, nullable=True)

    role = relationship("Role", back_populates="users")
