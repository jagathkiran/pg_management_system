from backend.app.database import SessionLocal, engine
from backend.app import models, auth

def create_admin():
    db = SessionLocal()
    try:
        email = "admin@pg.com"
        password = "admin"
        
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print("Creating admin user...")
            hashed_password = auth.get_password_hash(password)
            user = models.User(
                email=email,
                hashed_password=hashed_password,
                role=models.UserRole.ADMIN,
                is_active=True
            )
            db.add(user)
            db.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
