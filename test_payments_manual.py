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
from backend.app.models import User, UserRole, RoomType, Room, Tenant, PaymentStatus
from backend.app.auth import get_password_hash

# Setup test database
db_file = "./test_payments.db"
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
TEST_UPLOAD_FILE = "test_proof.jpg"
with open(TEST_UPLOAD_FILE, "wb") as f:
    f.write(b"fake image data")

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

def test_payments_flow():
    setup_data()
    
    # 1. Login as Tenant
    print("Logging in as Tenant...")
    tenant_token = get_token("tenant@example.com", "tenant123")
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}

    # 2. Upload Proof
    print("Uploading Payment Proof...")
    with open(TEST_UPLOAD_FILE, "rb") as f:
        response = client.post(
            "/api/payments/upload-proof",
            files={"file": (TEST_UPLOAD_FILE, f, "image/jpeg")},
            headers=tenant_headers
        )
    assert response.status_code == 200
    proof_data = response.json()
    assert "filename" in proof_data
    proof_path = proof_data["path"]
    print(f"File uploaded to: {proof_path}")

    # 3. Submit Payment
    print("Submitting Payment...")
    payment_data = {
        "amount": 5000.0,
        "payment_date": str(date.today()),
        "payment_method": "UPI",
        "transaction_id": "TXN123456789",
        "payment_month": str(date.today().replace(day=1)),
        "proof_image_path": proof_path
    }
    response = client.post("/api/payments/", json=payment_data, headers=tenant_headers)
    if response.status_code != 200:
        print(f"Submit failed: {response.json()}")
    assert response.status_code == 200
    payment_record = response.json()
    payment_id = payment_record["id"]
    assert payment_record["status"] == PaymentStatus.PENDING.value
    print(f"Payment submitted with ID: {payment_id}")

    # 4. List Own Payments (Tenant)
    print("Listing Own Payments...")
    response = client.get("/api/payments/", headers=tenant_headers)
    assert response.status_code == 200
    my_payments = response.json()
    assert len(my_payments) == 1
    assert my_payments[0]["id"] == payment_id

    # 5. Login as Admin
    print("Logging in as Admin...")
    admin_token = get_token("admin@example.com", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 6. List All Payments (Admin)
    print("Listing All Payments (Admin)...")
    response = client.get("/api/payments/", headers=admin_headers)
    assert response.status_code == 200
    all_payments = response.json()
    assert len(all_payments) == 1

    # 7. Verify Payment
    print("Verifying Payment...")
    verify_data = {
        "status": PaymentStatus.VERIFIED.value,
        "remarks": "Payment received successfully."
    }
    response = client.put(f"/api/payments/{payment_id}/verify", json=verify_data, headers=admin_headers)
    assert response.status_code == 200
    verified_payment = response.json()
    assert verified_payment["status"] == PaymentStatus.VERIFIED.value
    assert verified_payment["remarks"] == "Payment received successfully."
    print("Payment Verified.")

    # 8. Check Status as Tenant
    print("Checking Status as Tenant...")
    response = client.get(f"/api/payments/{payment_id}", headers=tenant_headers)
    assert response.status_code == 200
    assert response.json()["status"] == PaymentStatus.VERIFIED.value
    print("Tenant sees verified status.")

    # Cleanup
    if os.path.exists(TEST_UPLOAD_FILE):
        os.remove(TEST_UPLOAD_FILE)
    # Note: We are not cleaning up the 'uploads' folder or the uploaded file inside it in this test script 
    # to keep it simple, but in a real suite we should using a temp dir.

if __name__ == "__main__":
    try:
        test_payments_flow()
        print("\nAll PAYMENTS tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
