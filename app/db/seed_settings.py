from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.setting import Setting

def seed_settings():
    db_url = settings.DIRECT_URL if settings.DIRECT_URL else settings.get_database_url()
    engine = create_engine(db_url.replace("postgres://", "postgresql://"))
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        defaults = [
            {"key": "kpi_project_done_points", "value": "100", "category": "kpi", "description": "Points awarded for completing a project"},
            {"key": "kpi_large_project_bonus", "value": "20", "category": "kpi", "description": "Bonus points for projects > 10kWp"},
            {"key": "kpi_shipment_delivered_points", "value": "50", "category": "kpi", "description": "Points for successful shipment delivery"},
            {"key": "company_name", "value": "Antigravity ERP Solution", "category": "general", "description": "Display name of the company"},
            {"key": "low_stock_threshold", "value": "10", "category": "inventory", "description": "Threshold for low stock warnings"},
        ]
        
        for d in defaults:
            exists = db.query(Setting).filter(Setting.key == d["key"]).first()
            if not exists:
                setting = Setting(**d)
                db.add(setting)
        
        db.commit()
        print("✅ Default settings seeded.")
    except Exception as e:
        print(f"❌ Error seeding settings: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_settings()
