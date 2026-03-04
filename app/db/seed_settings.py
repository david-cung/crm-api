from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.setting import Setting

def seed_settings():
    db = SessionLocal()
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
