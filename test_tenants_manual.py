import os
import sys
from datetime import date

# Add project root to sys.path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, UserRole, RoomType, Room, Tenant
from backend.app.auth import get_password_hash

# Setup test database
db_file = "./test_tenants.db"
if os.path.exists(db_file):
    os.remove(db_file)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"
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

def setup_admin_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "admin@example.com").first()
    if not user:
        user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db.add(user)
        db.commit()
    db.close()

def get_admin_token():
    setup_admin_user()
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_tenants_flow():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a Room
    print("Creating Room 101...")
    room_data = {
        "room_number": "101",
        "floor": 1,
        "room_type": RoomType.SINGLE.value,
        "capacity": 1,
        "monthly_rent": 500.0
    }
    response = client.post("/api/rooms/", json=room_data, headers=headers)
    assert response.status_code == 201
    room_id = response.json()["id"]

    # 2. Register Tenant A
    print("Registering Tenant A...")
    tenant_a_data = {
        "full_name": "Tenant A",
        "email": "tenantA@example.com",
        "phone": "1234567890",
        "emergency_contact": "9876543210",
        "check_in_date": str(date.today()),
        "deposit_amount": 1000.0,
        "room_id": room_id
    }
    response = client.post("/api/tenants/", json=tenant_a_data, headers=headers)
    if response.status_code != 201:
        print(f"Register Tenant A failed: {response.json()}")
    assert response.status_code == 201
    tenant_a = response.json()
    tenant_a_id = tenant_a["id"]
    print(f"Tenant A registered with ID: {tenant_a_id}")
    
    # Verify email is in the nested user object
    assert tenant_a["user"]["email"] == "tenantA@example.com"

    # 3. Try to Register Tenant B (Should Fail - Room Full)
    print("Registering Tenant B (Should Fail)...")
    tenant_b_data = {
        "full_name": "Tenant B",
        "email": "tenantB@example.com",
        "phone": "1112223333",
        "emergency_contact": "4445556666",
        "check_in_date": str(date.today()),
        "deposit_amount": 1000.0,
        "room_id": room_id
    }
    response = client.post("/api/tenants/", json=tenant_b_data, headers=headers)
    assert response.status_code == 400
    assert "occupied" in response.json()["detail"].lower()
    print("Over-capacity check passed.")

    # 4. List Tenants
    print("Listing Tenants...")
    response = client.get("/api/tenants/", headers=headers)
    assert response.status_code == 200
    tenants = response.json()
    assert len(tenants) == 1
    assert tenants[0]["id"] == tenant_a_id

    # 5. Update Tenant A
    print("Updating Tenant A...")
    update_data = tenant_a_data.copy()
    update_data["phone"] = "0000000000"
    response = client.put(f"/api/tenants/{tenant_a_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["phone"] == "0000000000"
    print("Update passed.")

    # 6. Checkout Tenant A
    print("Checking out Tenant A...")
    response = client.post(f"/api/tenants/{tenant_a_id}/checkout", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] == False
    assert response.json()["check_out_date"] == str(date.today())
    print("Checkout passed.")

    # 7. Register Tenant B (Should Succeed now)
    print("Registering Tenant B (Should Succeed)...")
    response = client.post("/api/tenants/", json=tenant_b_data, headers=headers)
    if response.status_code != 201:
        print(f"Register Tenant B failed: {response.json()}")
    assert response.status_code == 201
    tenant_b_id = response.json()["id"]
    print("Tenant B registered.")

    # 8. List Tenants (Active Only)
    print("Listing Active Tenants...")
    response = client.get("/api/tenants/?active_only=true", headers=headers)
    tenants = response.json()
    assert len(tenants) == 1
    assert tenants[0]["id"] == tenant_b_id

    # 9. List All Tenants
    print("Listing All Tenants...")
    response = client.get("/api/tenants/?active_only=false", headers=headers)
    tenants = response.json()
    assert len(tenants) == 2
    ids = [t["id"] for t in tenants]
    assert tenant_a_id in ids
    assert tenant_b_id in ids

if __name__ == "__main__":
    try:
        test_tenants_flow()
        print("\nAll TENANTS tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
