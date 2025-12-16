import requests
from datetime import date

BASE_URL = "http://localhost:8000/api"

def test_reports():
    print("Logging in as Admin...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@pg.com", "password": "admin"})
    if resp.status_code != 200:
        print("Admin login failed.")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test Revenue Report
    print("\nTesting Revenue Report...")
    resp = requests.get(f"{BASE_URL}/reports/revenue", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Total Revenue: {data.get('total_revenue')}")
        print(f"Pending Revenue: {data.get('pending_revenue')}")
        print(f"Monthly Breakdown: {data.get('monthly_breakdown')}")
    else:
        print(f"Failed: {resp.text}")

    # 2. Test Occupancy Report
    print("\nTesting Occupancy Report...")
    resp = requests.get(f"{BASE_URL}/reports/occupancy", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Occupancy Rate: {data.get('occupancy_rate')}%")
        print(f"Vacant Rooms: {data.get('vacant_rooms_count')}")
    else:
        print(f"Failed: {resp.text}")

    # 3. Test Tenant Report (need a tenant ID)
    # Fetch list of tenants first
    tenants = requests.get(f"{BASE_URL}/tenants/", headers=headers).json()
    if tenants:
        tenant_id = tenants[0]['id']
        print(f"\nTesting Tenant Report for ID {tenant_id}...")
        resp = requests.get(f"{BASE_URL}/reports/tenant/{tenant_id}", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("Tenant Details:", data.get('tenant_details'))
            print("Financials:", data.get('financials'))
        else:
            print(f"Failed: {resp.text}")
    else:
        print("\nSkipping Tenant Report (No tenants found)")

if __name__ == "__main__":
    test_reports()
