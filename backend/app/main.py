from fastapi import FastAPI
from backend.app.routers import auth, rooms
from backend.app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PG Management System")

app.include_router(auth.router)
app.include_router(rooms.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to PG Management System API"}
