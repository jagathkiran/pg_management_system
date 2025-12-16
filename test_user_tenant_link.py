import requests
from datetime import date

BASE_URL = "http://localhost:8000/api"

def test_user_tenant_link():
    # 1. Login as Admin
    print("Logging in as Admin...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@pg.com", "password": "admin"})
    if resp.status_code != 200:
        print("Admin login failed. Make sure server is running and admin exists.")
        return
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create a Room (if needed, but assuming some exist or we can create one)
    # Let's create a dummy room
    print("Creating dummy room...")
    room_data = {
        "room_number": "T999",
        "floor": 1,
        "room_type": "Single",
        "capacity": 1,
        "monthly_rent": 5000
    }
    # Ignore error if exists
    requests.post(f"{BASE_URL}/rooms/", json=room_data, headers=admin_headers)
    
    # Get room ID
    rooms = requests.get(f"{BASE_URL}/rooms/", headers=admin_headers).json()
    room_id = next((r['id'] for r in rooms if r['room_number'] == "T999"), None)

    # 3. Create a Tenant
    print("Creating tenant...")
    unique_email = f"tenant_test_{date.today()}@example.com"
    # Cleanup previous run?
    # Hard to cleanup user in this simple script without direct DB access or delete endpoint.
    # We'll use random email.
    import time
    unique_email = f"tenant_{int(time.time())}@example.com"
    
    tenant_data = {
        "full_name": "Test Tenant",
        "email": unique_email,
        "phone": "1234567890",
        "emergency_contact": "0987654321",
        "check_in_date": str(date.today()),
        "deposit_amount": 1000,
        "room_id": room_id,
        "password": "password123"
    }
    
    resp = requests.post(f"{BASE_URL}/tenants/", json=tenant_data, headers=admin_headers)
    if resp.status_code != 201:
        print(f"Tenant creation failed: {resp.text}")
        return
    tenant_id = resp.json()["id"]
    print(f"Tenant created with ID: {tenant_id}")

    # 4. Login as Tenant
    print("Logging in as Tenant...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": unique_email, "password": "password123"})
    if resp.status_code != 200:
        print(f"Tenant login failed: {resp.text}")
        return
    tenant_token = resp.json()["access_token"]
    tenant_headers = {"Authorization": f"Bearer {tenant_token}"}

    # 5. Get /auth/me
    print("Fetching /auth/me ...")
    resp = requests.get(f"{BASE_URL}/auth/me", headers=tenant_headers)
    if resp.status_code != 200:
        print(f"Failed to fetch me: {resp.text}")
        return
    
    user_data = resp.json()
    print("User Data received:")
    # print(user_data)
    
    if "tenant" in user_data and user_data["tenant"]:
        print("SUCCESS: 'tenant' field found in UserResponse.")
        print(f"Tenant Name: {user_data['tenant']['full_name']}")
        if user_data['tenant']['id'] == tenant_id:
             print("SUCCESS: Tenant ID matches.")
        else:
             print("FAILURE: Tenant ID mismatch.")
    else:
        print("FAILURE: 'tenant' field missing or empty.")

if __name__ == "__main__":
    test_user_tenant_link()
