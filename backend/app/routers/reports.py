from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from backend.app import database, models, schemas, dependencies
from backend.app.database import get_db
from backend.app.routers.rooms import get_room_occupancy, is_room_available

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"]
)

# --- Schemas for Reports (Internal to this file or could be in schemas.py) ---
# For simplicity, returning Dicts or specific Pydantic models if needed.

@router.get("/revenue", response_model=Dict[str, Any])
def get_revenue_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_admin_user)
):
    """
    Get revenue statistics: Total collected, Pending, and Monthly breakdown.
    Optional date range filtering affects the 'Total' and 'Pending' calculation context 
    and the range of the monthly breakdown.
    """
    query = db.query(models.RentPayment)
    
    if start_date:
        query = query.filter(models.RentPayment.payment_date >= start_date)
    if end_date:
        query = query.filter(models.RentPayment.payment_date <= end_date)
        
    payments = query.all()
    
    total_revenue = sum(p.amount for p in payments if p.status == models.PaymentStatus.VERIFIED.value)
    pending_revenue = sum(p.amount for p in payments if p.status == models.PaymentStatus.PENDING.value)
    
    # Monthly Breakdown (Group by Year-Month)
    # Using python for grouping to avoid complex SQL dialects differences (SQLite vs Postgres) for date extraction
    monthly_data = {}
    
    for p in payments:
        if p.status == models.PaymentStatus.VERIFIED.value:
            # key = YYYY-MM
            month_key = p.payment_month.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = 0.0
            monthly_data[month_key] += p.amount
            
    # Sort by month
    sorted_monthly = [{"month": k, "revenue": v} for k, v in sorted(monthly_data.items())]

    return {
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue,
        "monthly_breakdown": sorted_monthly,
        "period": {
            "start": start_date,
            "end": end_date
        }
    }

@router.get("/occupancy", response_model=Dict[str, Any])
def get_occupancy_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user) # Allow tenants to see availability? Or Admin only? Plan says "cancelled" so I'll assume admin for detailed report.
):
    # Actually, allow tenants to see general occupancy might be fine, but let's stick to Admin for detailed lists.
    # The current_user dependency is mainly for auth check. 
    # If explicit permission needed:
    if current_user.role != models.UserRole.ADMIN.value:
         pass # Maybe restrict full lists? For now, let's allow basic visibility or restrict whole endpoint.
         # Let's restrict to Admin for the "Reports" module generally.
         if current_user.role != models.UserRole.ADMIN.value:
             raise HTTPException(status_code=403, detail="Not authorized")

    rooms = db.query(models.Room).filter(models.Room.is_active == True).all()
    
    total_capacity = sum(r.capacity for r in rooms)
    total_rooms = len(rooms)
    
    # Calculate occupied beds
    # We can iterate rooms and use get_room_occupancy helper
    occupied_beds = 0
    vacant_rooms_list = []
    occupied_rooms_list = []
    
    for room in rooms:
        occ = get_room_occupancy(room)
        occupied_beds += occ
        
        room_data = {
            "id": room.id,
            "room_number": room.room_number,
            "type": room.room_type,
            "capacity": room.capacity,
            "occupancy": occ
        }
        
        if occ > 0:
            occupied_rooms_list.append(room_data)
        
        if occ < room.capacity:
            vacant_rooms_list.append(room_data)
            
    occupancy_rate = 0.0
    if total_capacity > 0:
        occupancy_rate = (occupied_beds / total_capacity) * 100
        
    return {
        "occupancy_rate": round(occupancy_rate, 2),
        "total_capacity": total_capacity,
        "total_occupied_beds": occupied_beds,
        "total_rooms": total_rooms,
        "vacant_rooms_count": len(vacant_rooms_list),
        "occupied_rooms_count": len(occupied_rooms_list),
        "vacant_rooms": vacant_rooms_list,
        "occupied_rooms": occupied_rooms_list
    }

@router.get("/tenant/{tenant_id}", response_model=Dict[str, Any])
def get_tenant_report(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_admin_user)
):
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    # Payments
    payments = db.query(models.RentPayment).filter(models.RentPayment.tenant_id == tenant_id).all()
    total_paid = sum(p.amount for p in payments if p.status == models.PaymentStatus.VERIFIED.value)
    pending_amount = sum(p.amount for p in payments if p.status == models.PaymentStatus.PENDING.value)
    
    # Maintenance
    maintenance_reqs = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.tenant_id == tenant_id).all()
    open_requests = len([r for r in maintenance_reqs if r.status in [models.MaintenanceStatus.OPEN.value, models.MaintenanceStatus.IN_PROGRESS.value]])
    resolved_requests = len([r for r in maintenance_reqs if r.status in [models.MaintenanceStatus.RESOLVED.value, models.MaintenanceStatus.CLOSED.value]])
    
    return {
        "tenant_details": {
            "full_name": tenant.full_name,
            "email": tenant.user.email if tenant.user else None,
            "phone": tenant.phone,
            "room": tenant.room.room_number if tenant.room else "Unassigned",
            "check_in": tenant.check_in_date,
            "status": "Active" if tenant.is_active else "Inactive"
        },
        "financials": {
            "total_rent_paid": total_paid,
            "pending_dues": pending_amount,
            "payment_history_count": len(payments)
        },
        "maintenance": {
            "total_requests": len(maintenance_reqs),
            "open": open_requests,
            "resolved": resolved_requests
        },
        "history": {
            "payments": [
                {
                    "date": p.payment_date,
                    "amount": p.amount,
                    "month": p.payment_month,
                    "status": p.status
                } for p in payments
            ],
            "maintenance": [
                {
                    "id": m.id,
                    "date": m.request_date,
                    "category": m.category,
                    "status": m.status
                } for m in maintenance_reqs
            ]
        }
    }
