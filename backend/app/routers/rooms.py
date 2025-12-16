from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app import models, schemas, dependencies
from backend.app.database import get_db

router = APIRouter(
    prefix="/api/rooms",
    tags=["rooms"],
    responses={404: {"description": "Not found"}},
)

# Helper function to calculate occupancy
def get_room_occupancy(room: models.Room) -> int:
    return len([t for t in room.tenants if t.is_active])

def is_room_available(room: models.Room) -> bool:
    occupancy = get_room_occupancy(room)
    return occupancy < room.capacity

@router.get("/", response_model=List[schemas.RoomResponse])
def read_rooms(
    skip: int = 0,
    limit: int = 100,
    available: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """
    Retrieve all rooms with pagination and optional availability filter.
    """
    query = db.query(models.Room).filter(models.Room.is_active == True)
    
    rooms = query.all() # Fetch all to filter by python logic for availability or use complex query
    
    # Filter by availability if requested
    if available is not None:
        filtered_rooms = []
        for room in rooms:
            if is_room_available(room) == available:
                filtered_rooms.append(room)
        rooms = filtered_rooms
    
    # Apply pagination manually if filtered, or use slice
    return rooms[skip : skip + limit]

@router.post("/", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_admin_user)
):
    """
    Create a new room. Admin only.
    """
    db_room = db.query(models.Room).filter(models.Room.room_number == room.room_number).first()
    if db_room:
        raise HTTPException(status_code=400, detail="Room already exists")
    
    new_room = models.Room(**room.dict())
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room

@router.get("/available", response_model=List[schemas.RoomResponse])
def read_available_rooms(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """
    Retrieve all available rooms (capacity > current occupancy).
    """
    all_rooms = db.query(models.Room).filter(models.Room.is_active == True).all()
    available_rooms = [room for room in all_rooms if is_room_available(room)]
    return available_rooms

@router.get("/occupied", response_model=List[schemas.RoomResponse])
def read_occupied_rooms(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """
    Retrieve all occupied rooms (current occupancy > 0).
    """
    all_rooms = db.query(models.Room).filter(models.Room.is_active == True).all()
    occupied_rooms = [room for room in all_rooms if get_room_occupancy(room) > 0]
    return occupied_rooms

@router.get("/{room_id}", response_model=schemas.RoomResponse)
def read_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    """
    Get a specific room by ID.
    """
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.put("/{room_id}", response_model=schemas.RoomResponse)
def update_room(
    room_id: int,
    room_update: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_admin_user)
):
    """
    Update a room. Admin only.
    """
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room number is being changed to one that already exists
    if room_update.room_number != db_room.room_number:
        existing_room = db.query(models.Room).filter(models.Room.room_number == room_update.room_number).first()
        if existing_room:
             raise HTTPException(status_code=400, detail="Room number already registered")

    # Check capacity validation
    current_occupancy = get_room_occupancy(db_room)
    if room_update.capacity < current_occupancy:
        raise HTTPException(status_code=400, detail=f"Cannot reduce capacity below current occupancy ({current_occupancy})")

    for key, value in room_update.dict().items():
        setattr(db_room, key, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_admin_user)
):
    """
    Delete (soft delete) a room. Admin only.
    """
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room has active tenants
    occupancy = get_room_occupancy(room)
    if occupancy > 0:
        raise HTTPException(status_code=400, detail="Cannot delete room with active tenants")

    # Hard delete or soft delete? Model has is_active. Let's use soft delete convention unless specified.
    # But usually DELETE verb implies removal. However, for integrity, soft delete is safer.
    # The models.Room has is_active.
    # Let's check the plan. "Delete room - admin only".
    # I'll implement hard delete for now but ensure no dependencies, or just set is_active=False.
    # Actually, previous endpoints filter by is_active=True. So setting is_active=False is a valid "delete".
    
    room.is_active = False
    db.commit()
    return None
