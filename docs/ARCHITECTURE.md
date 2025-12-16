# System Architecture

## Component Overview

### Frontend (Streamlit)

- **`app.py`**: Main entry point, handles initial routing and authentication sidebar.
- **`pages/`**: Contains individual page views (`login.py`, `signup.py`, `management_dashboard.py`, `tenant_dashboard.py`).
- **`components/`**: Reusable UI modules for specific features (e.g., `room_management.py`, `payment_submission.py`).
- **`utils/`**: Helper functions for API communication (`api_client.py`) and session management (`session.py`, `ui.py`).

### Backend (FastAPI)

- **`main.py`**: Application entry point, configures CORS and includes routers.
- **`routers/`**: Defines API endpoints grouped by functionality (`auth`, `rooms`, `tenants`, `payments`, `maintenance`).
- **`models.py`**: SQLAlchemy ORM models defining the database schema.
- **`schemas.py`**: Pydantic models for request validation and response serialization.
- **`database.py`**: Database connection and session management.
- **`auth.py`**: JWT token generation and password hashing utilities.
