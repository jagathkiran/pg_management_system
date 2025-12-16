import os
import sys

# Add project root to sys.path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, UserRole, RoomType, Room
from backend.app.auth import get_password_hash

# Setup test database
db_file = "./test_rooms.db"
if os.path.exists(db_file):
    os.remove(db_file)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base.metadata.drop_all(bind=engine) # Not needed if file removed
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
print(f"Overrides: {app.dependency_overrides}")

client = TestClient(app)

def setup_admin_user():
    db = TestingSessionLocal()
    # Debug: Check rooms
    rooms = db.query(Room).all()
    print(f"DEBUG: Rooms in DB before test: {len(rooms)}")
    
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

def test_rooms_crud():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Room
    print("Testing Create Room...")
    room_data = {
        "room_number": "101",
        "floor": 1,
        "room_type": RoomType.SINGLE.value,
        "capacity": 1,
        "monthly_rent": 500.0
    }
    response = client.post("/api/rooms/", json=room_data, headers=headers)
    if response.status_code != 201:
        print(f"Create Room failed: {response.json()}")
    assert response.status_code == 201
    room_id = response.json()["id"]
    print(f"Room created with ID: {room_id}")

    # 2. Create Duplicate Room (Should Fail)
    print("Testing Duplicate Room Creation...")
    response = client.post("/api/rooms/", json=room_data, headers=headers)
    assert response.status_code == 400
    print("Duplicate room check passed.")

    # 3. List Rooms
    print("Testing List Rooms...")
    response = client.get("/api/rooms/", headers=headers)
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) >= 1
    assert rooms[0]["room_number"] == "101"
    print("List rooms passed.")

    # 4. Get Specific Room
    print("Testing Get Room Details...")
    response = client.get(f"/api/rooms/{room_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == room_id
    print("Get room details passed.")

    # 5. Update Room
    print("Testing Update Room...")
    update_data = {
        "room_number": "101",
        "floor": 1,
        "room_type": RoomType.SINGLE.value,
        "capacity": 2, # Changed capacity
        "monthly_rent": 600.0 # Changed rent
    }
    response = client.put(f"/api/rooms/{room_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    updated_room = response.json()
    assert updated_room["monthly_rent"] == 600.0
    assert updated_room["capacity"] == 2
    print("Update room passed.")

    # 6. Check Available Rooms
    print("Testing Available Rooms...")
    response = client.get("/api/rooms/available", headers=headers)
    assert response.status_code == 200
    available = response.json()
    # Since we created one room with capacity 2 and 0 tenants, it should be available
    assert any(r["id"] == room_id for r in available)
    print("Available rooms passed.")

    # 7. Delete Room
    print("Testing Delete Room...")
    response = client.delete(f"/api/rooms/{room_id}", headers=headers)
    assert response.status_code == 204
    print("Delete room passed.")

    # 8. Verify Deletion (Soft Delete check in List)
    print("Verifying Deletion in List...")
    response = client.get("/api/rooms/", headers=headers)
    rooms = response.json()
    # Should not contain the deleted room
    assert not any(r["id"] == room_id for r in rooms)
    print("Verification passed.")

if __name__ == "__main__":
    try:
        test_rooms_crud()
        print("\nAll ROOMS tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
