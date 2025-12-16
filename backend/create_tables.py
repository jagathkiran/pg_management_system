import sys
import os

# Get the directory of the current script (backend/create_tables.py)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (one level up from 'backend')
project_root = os.path.dirname(script_dir)
# Add the project root to the Python path
sys.path.insert(0, project_root)

from backend.app.database import engine, Base
from backend.app import models # noqa: F401 for importing models to be registered with Base

def create_db_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    create_db_tables()
