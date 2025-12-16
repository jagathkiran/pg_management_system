import sys
import os
import time

# Ensure we can import from frontend/utils
current_dir = os.getcwd()
frontend_dir = os.path.join(current_dir, 'frontend')
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from utils.api_client import APIClient

def test_connectivity():
    print("Testing API Client...")
    # APIClient expects base_url. Default in app.py is http://localhost:8000/api
    client = APIClient(base_url="http://localhost:8000/api")
    
    # Wait for server to start (we'll run this script after starting server in background)
    max_retries = 10
    for i in range(max_retries):
        connected = client.check_connection()
        if connected:
            print("Successfully connected to Backend API!")
            return True
        print(f"Connection attempt {i+1} failed. Retrying in 1 second...")
        time.sleep(1)
        
    print("Failed to connect to Backend API after multiple attempts.")
    return False

if __name__ == "__main__":
    if test_connectivity():
        sys.exit(0)
    else:
        sys.exit(1)
