# PG Management System

A comprehensive Property Management System designed for Paying Guest (PG) accommodations. This application provides a full-stack solution with a FastAPI backend and a Streamlit frontend, enabling administrators to manage rooms, tenants, payments, and maintenance requests, while offering a dedicated dashboard for tenants.

## 📋 Features

### 👑 Admin Module
- **Dashboard**: Overview of financials, occupancy, and pending tasks.
- **Room Management**: Add, update, and track room availability and occupancy.
- **Tenant Management**: Register tenants, link them to rooms, and manage their profiles.
- **Payment Collection**: Verify rent payments submitted by tenants, view history, and generate reports.
- **Maintenance**: Track and update status of maintenance requests raised by tenants.
- **Reports**: Generate financial and occupancy reports.

### 🏠 Tenant Module
- **Dashboard**: Personal overview of rent status and requests.
- **Profile**: View and manage personal details.
- **Pay Rent**: Upload payment proofs (screenshots) and submit rent details.
- **Maintenance**: Submit maintenance requests with descriptions and images.
- **Notifications**: Receive updates on payment verification and request status.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy (ORM), Pydantic (Validation), SQLite (Database).
- **Frontend**: Streamlit (Python-based UI).
- **Authentication**: JWT (JSON Web Tokens) with role-based access control (RBAC).
- **Storage**: Local filesystem for image uploads (proofs/maintenance).

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- `pip` (Python package manager)

### Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    pip install -r frontend/requirements.txt
    ```

4.  **Environment Setup**:
    Create a `.env` file in the root directory (copy from `.env.example` if available) or set environment variables directly. The defaults usually work for local development.
    ```bash
    cp .env.example .env
    ```

### Running the Application

You need to run both the Backend (API) and Frontend (UI) servers.

#### 1. Start the Backend Server
```bash
uvicorn backend.app.main:app --reload
```
The API will be available at `http://localhost:8000`.
API Documentation (Swagger UI): `http://localhost:8000/docs`

#### 2. Start the Frontend Application
Open a new terminal, activate the virtual environment, and run:
```bash
streamlit run frontend/app.py
```
The application will open in your browser at `http://localhost:8501`.

## 📂 Project Structure

```
pg_management/
├── backend/            # FastAPI Backend
│   ├── app/
│   │   ├── routers/    # API Endpoints (auth, rooms, tenants, etc.)
│   │   ├── models.py   # Database Models
│   │   ├── schemas.py  # Pydantic Schemas
│   │   └── ...
│   └── ...
├── frontend/           # Streamlit Frontend
│   ├── pages/          # Application Pages (Login, Dashboard, etc.)
│   ├── components/     # Reusable UI Components
│   └── utils/          # Helper functions (API Client, Session)
├── database/           # SQLite Database file
├── docs/               # Documentation (Architecture, etc.)
└── uploads/            # Uploaded files directory
```

## 📖 Documentation
For detailed system architecture, data flow diagrams, and control flow diagrams, please refer to [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🧪 Testing
To run the verification scripts:
```bash
python test_auth_manual.py
# (and other test_*.py scripts in the root)
```

## 🔐 Default Credentials
*(For testing purposes only - Change immediately in production)*
- **Admin**: Create via Sign Up page or `backend/create_admin.py`.
- **Tenant**: Register via Sign Up page.

---
Built with ❤️ using Python.
