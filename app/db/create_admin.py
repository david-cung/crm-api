from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User, UserType
from app.core.security import get_password_hash

def create_admin():
    db_url = settings.DIRECT_URL if settings.DIRECT_URL else settings.get_database_url()
    engine = create_engine(db_url.replace("postgres://", "postgresql://"))
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        admin_email = "admin@erp.com"
        exists = db.query(User).filter(User.email == admin_email).first()
        if not exists:
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                is_active=True,
                is_superuser=True,
                phone_number="0000000000",
                user_type=UserType.WEB_ADMIN
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin user created: {admin_email} / admin123")
        else:
            print(f"ℹ️ Admin user already exists: {admin_email}")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
