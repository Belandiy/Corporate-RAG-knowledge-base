from sqlalchemy.orm import Session
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, UserRole
from app.core.config import settings
import bcrypt

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_db():
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    
    # Создаем админа по умолчанию
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USER).first()
        if not admin:
            admin_user = User(
                username=settings.DEFAULT_ADMIN_USER,
                password_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                role=UserRole.ADMIN.value
            )
            db.add(admin_user)
            db.commit()
            print(f"Admin user '{settings.DEFAULT_ADMIN_USER}' created.")
        else:
            print(f"Admin user '{settings.DEFAULT_ADMIN_USER}' already exists.")
    except Exception as e:
        print(f"Error initializing DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
