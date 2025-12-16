import os
import sys

# Add project root to sys.path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.dependencies import get_db
from backend.app.database import Base
from backend.app.models import User, UserRole
from backend.app.auth import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def setup_test_user():
    db = TestingSessionLocal()
    # Check if user exists
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db.add(user)
        db.commit()
    db.close()

def test_login():
    setup_test_user()
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_me(token):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print(f"Me failed: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "admin"
    print("User retrieved successfully:", data)

if __name__ == "__main__":
    try:
        print("Testing Login...")
        token = test_login()
        print("Login Successful. Token received.")
        
        print("Testing /me endpoint...")
        test_me(token)
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
