import os
import sys
from datetime import date
import shutil

# Add project root to sys.path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, UserRole, RoomType, Room, Tenant, MaintenancePriority, MaintenanceCategory, MaintenanceStatus
from backend.app.auth import get_password_hash

# Setup test database
db_file = "./test_maintenance.db"
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

# Dummy file for upload test
TEST_UPLOAD_FILE = "test_maintenance_img.jpg"
with open(TEST_UPLOAD_FILE, "wb") as f:
    f.write(b"fake maintenance image data")

def setup_data():
    db = TestingSessionLocal()
    
    # 1. Admin
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db.add(admin)
    
    # 2. Room
    room = db.query(Room).filter(Room.room_number == "101").first()
    if not room:
        room = Room(
            room_number="101",
            floor=1,
            room_type=RoomType.SINGLE.value,
            capacity=1,
            monthly_rent=5000.0,
            is_active=True
        )
        db.add(room)
        db.commit() # Commit to get ID
    
    # 3. Tenant User & Tenant
    tenant_user = db.query(User).filter(User.email == "tenant@example.com").first()
    if not tenant_user:
        tenant_user = User(
            email="tenant@example.com",
            hashed_password=get_password_hash("tenant123"),
            role=UserRole.TENANT.value,
            is_active=True
        )
        db.add(tenant_user)
        db.flush()
        
        tenant = Tenant(
            user_id=tenant_user.id,
            room_id=room.id,
            full_name="Test Tenant",
            phone="1234567890",
            emergency_contact="0987654321",
            check_in_date=date.today(),
            deposit_amount=10000.0,
            is_active=True
        )
        db.add(tenant)
    
    db.commit()
    db.close()

def get_token(email, password):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_maintenance_flow():
    setup_data()
    
    # 1. Login as Tenant
    print("Logging in as Tenant...")
    tenant_token = get_token("tenant@example.com", "tenant123")
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}

    # 2. Upload Image
    print("Uploading Maintenance Image...")
    with open(TEST_UPLOAD_FILE, "rb") as f:
        response = client.post(
            "/api/maintenance/upload-image",
            files={"file": (TEST_UPLOAD_FILE, f, "image/jpeg")},
            headers=tenant_headers
        )
    assert response.status_code == 200
    proof_data = response.json()
    assert "filename" in proof_data
    image_path = proof_data["path"]
    print(f"File uploaded to: {image_path}")

    # 3. Create Request
    print("Creating Maintenance Request...")
    req_data = {
        "category": MaintenanceCategory.PLUMBING.value,
        "priority": MaintenancePriority.HIGH.value,
        "description": "Leaky faucet in bathroom",
        "image_path": image_path
    }
    response = client.post("/api/maintenance/", json=req_data, headers=tenant_headers)
    if response.status_code != 200:
        print(f"Create failed: {response.json()}")
    assert response.status_code == 200
    req_record = response.json()
    req_id = req_record["id"]
    assert req_record["status"] == MaintenanceStatus.OPEN.value
    print(f"Request created with ID: {req_id}")

    # 4. List Own Requests (Tenant)
    print("Listing Own Requests...")
    response = client.get("/api/maintenance/", headers=tenant_headers)
    assert response.status_code == 200
    my_reqs = response.json()
    assert len(my_reqs) == 1
    assert my_reqs[0]["id"] == req_id

    # 5. Login as Admin
    print("Logging in as Admin...")
    admin_token = get_token("admin@example.com", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 6. List All Requests (Admin)
    print("Listing All Requests (Admin)...")
    response = client.get("/api/maintenance/", headers=admin_headers)
    assert response.status_code == 200
    all_reqs = response.json()
    assert len(all_reqs) == 1

    # 7. Update Request (Admin)
    print("Updating Request Status...")
    update_data = {
        "status": MaintenanceStatus.RESOLVED.value,
        "resolution_notes": "Fixed the leak by replacing washer."
    }
    response = client.put(f"/api/maintenance/{req_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200
    updated_req = response.json()
    assert updated_req["status"] == MaintenanceStatus.RESOLVED.value
    assert updated_req["resolution_notes"] == "Fixed the leak by replacing washer."
    assert updated_req["resolved_date"] is not None
    print("Request Updated.")

    # 8. Check Status as Tenant
    print("Checking Status as Tenant...")
    response = client.get(f"/api/maintenance/{req_id}", headers=tenant_headers)
    assert response.status_code == 200
    assert response.json()["status"] == MaintenanceStatus.RESOLVED.value
    print("Tenant sees resolved status.")

    # 9. Check Stats (Admin)
    print("Checking Maintenance Stats...")
    response = client.get("/api/maintenance/stats", headers=admin_headers)
    assert response.status_code == 200
    stats = response.json()
    print(f"Stats: {stats}")
    assert "status_counts" in stats
    assert "category_counts" in stats
    assert "avg_resolution_time_hours" in stats
    
    # Since we just resolved one, we should have stats
    assert stats["status_counts"][MaintenanceStatus.RESOLVED.value] == 1
    assert stats["category_counts"][MaintenanceCategory.PLUMBING.value] == 1
    # Resolution time might be near 0 since test runs fast, but should be present

    # Cleanup
    if os.path.exists(TEST_UPLOAD_FILE):
        os.remove(TEST_UPLOAD_FILE)
    # Note: We are not cleaning up the 'uploads' folder or the uploaded file inside it

if __name__ == "__main__":
    try:
        test_maintenance_flow()
        print("\nAll MAINTENANCE tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
