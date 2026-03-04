from sqlalchemy import Column, Integer, String, Float
from app.db.base_class import Base

class InventoryItem(Base):
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    quantity = Column(Integer, default=0, nullable=False)
    min_quantity = Column(Integer, default=5)
    unit_price = Column(Float, nullable=False)
    category = Column(String, index=True) # e.g. "Solar", "Camera", "General"
