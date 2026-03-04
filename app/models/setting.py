from sqlalchemy import Column, Integer, String, Text
from app.db.base_class import Base

class Setting(Base):
    __tablename__ = "setting"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    category = Column(String(50), index=True, default="general") # general, kpi, notification
