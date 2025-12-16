from fastapi import FastAPI
from backend.app.routers import auth, rooms, tenants, payments, maintenance, reports
from backend.app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PG Management System")

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(tenants.router)
app.include_router(payments.router)
app.include_router(maintenance.router)
app.include_router(reports.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to PG Management System API"}
