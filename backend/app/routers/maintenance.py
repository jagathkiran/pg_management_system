from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import shutil
import os
import uuid

from backend.app import database, models, schemas
from backend.app.dependencies import get_current_active_user, get_current_admin_user, get_db

router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"]
)

UPLOAD_DIR = "uploads/maintenance"

@router.post("/upload-image", response_model=dict)
async def upload_maintenance_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user)
):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": unique_filename, "path": file_path}

@router.post("/", response_model=schemas.MaintenanceRequestResponse)
def create_maintenance_request(
    request: schemas.MaintenanceBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.TENANT.value:
         raise HTTPException(status_code=403, detail="Only tenants can submit maintenance requests")
    
    if not current_user.tenant:
         raise HTTPException(status_code=400, detail="User is not associated with a tenant record")
    
    if not current_user.tenant.room_id:
        raise HTTPException(status_code=400, detail="You must be assigned to a room to create a maintenance request")

    db_request = models.MaintenanceRequest(
        tenant_id=current_user.tenant.id,
        **request.model_dump()
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/", response_model=List[schemas.MaintenanceRequestResponse])
def read_maintenance_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.MaintenanceStatus] = None,
    priority: Optional[models.MaintenancePriority] = None,
    category: Optional[models.MaintenanceCategory] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.MaintenanceRequest)
    
    if current_user.role == models.UserRole.TENANT.value:
        # Tenant can only see their own
        if not current_user.tenant:
            return []
        query = query.filter(models.MaintenanceRequest.tenant_id == current_user.tenant.id)
        
    if status:
        query = query.filter(models.MaintenanceRequest.status == status.value)
    if priority:
        query = query.filter(models.MaintenanceRequest.priority == priority.value)
    if category:
        query = query.filter(models.MaintenanceRequest.category == category.value)
        
    requests = query.offset(skip).limit(limit).all()
    return requests

@router.get("/stats", dependencies=[Depends(get_current_admin_user)])
def get_maintenance_stats(db: Session = Depends(get_db)):
    # Count by status
    status_counts = db.query(
        models.MaintenanceRequest.status, func.count(models.MaintenanceRequest.id)
    ).group_by(models.MaintenanceRequest.status).all()
    
    # Count by category
    category_counts = db.query(
        models.MaintenanceRequest.category, func.count(models.MaintenanceRequest.id)
    ).group_by(models.MaintenanceRequest.category).all()
    
    # Calculate average resolution time (for resolved requests)
    # This might differ between DBs (SQLite vs Postgres). 
    # For SQLite, calculating date diffs in SQL is tricky. 
    # Since we are likely using SQLite for dev, let's do it in python for simplicity if dataset is small, 
    # or try a compatible SQL query.
    # Given this is a prototype/MVP, Python calculation for avg time is acceptable for now.
    
    resolved_requests = db.query(models.MaintenanceRequest).filter(
        models.MaintenanceRequest.status.in_([models.MaintenanceStatus.RESOLVED.value, models.MaintenanceStatus.CLOSED.value]),
        models.MaintenanceRequest.resolved_date.isnot(None)
    ).all()
    
    total_resolution_time = 0
    resolved_count = 0
    for req in resolved_requests:
        if req.request_date and req.resolved_date:
            # request_date might be timezone aware, resolved_date too.
            # Ensure compatibility.
            diff = req.resolved_date - req.request_date
            total_resolution_time += diff.total_seconds()
            resolved_count += 1
            
    avg_resolution_hours = 0
    if resolved_count > 0:
        avg_resolution_hours = (total_resolution_time / resolved_count) / 3600

    return {
        "status_counts": {s: c for s, c in status_counts},
        "category_counts": {c: count for c, count in category_counts},
        "avg_resolution_time_hours": round(avg_resolution_hours, 2)
    }

@router.get("/{request_id}", response_model=schemas.MaintenanceRequestResponse)
def read_maintenance_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    request = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.id == request_id).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
        
    if current_user.role == models.UserRole.TENANT.value:
        if not current_user.tenant or request.tenant_id != current_user.tenant.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
            
    return request

@router.put("/{request_id}", response_model=schemas.MaintenanceRequestResponse)
def update_maintenance_request(
    request_id: int,
    update_data: schemas.MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    request = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.id == request_id).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    
    if update_data.status:
        request.status = update_data.status.value
        # If status is changing to RESOLVED or CLOSED, set resolved_date
        if update_data.status in [models.MaintenanceStatus.RESOLVED, models.MaintenanceStatus.CLOSED]:
             request.resolved_date = datetime.now()
        # If status is changing back to OPEN/IN_PROGRESS from resolved, maybe clear resolved_date?
        # Let's keep it simple for now.
        
    if update_data.resolution_notes:
        request.resolution_notes = update_data.resolution_notes
        
    db.commit()
    db.refresh(request)
    return request
