from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import shutil
import os
import uuid

from backend.app import database, models, schemas
from backend.app.dependencies import get_current_active_user, get_current_admin_user, get_db

router = APIRouter(
    prefix="/api/payments",
    tags=["payments"]
)

UPLOAD_DIR = "uploads"

@router.post("/upload-proof", response_model=dict)
async def upload_payment_proof(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user)
):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": unique_filename, "path": file_path}

@router.post("/", response_model=schemas.RentPaymentResponse)
def create_payment(
    payment: schemas.PaymentBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # If user is admin, they might be submitting for a tenant, but the current Schema assumes
    # PaymentBase + logic. 
    # If user is tenant, we use their tenant_id.
    
    tenant_id = None
    if current_user.role == models.UserRole.TENANT.value:
        if not current_user.tenant:
             raise HTTPException(status_code=400, detail="User is not associated with a tenant record")
        tenant_id = current_user.tenant.id
    else:
        # Admin is submitting? 
        # Ideally, admin should provide tenant_id. 
        # But PaymentBase doesn't have tenant_id.
        # For now, let's assume this endpoint is primarily for tenants to submit THEIR payment.
        # If admin wants to record a payment, they might need a separate endpoint or we check if they passed a tenant_id
        # (which isn't in PaymentBase).
        # Let's enforce: Only tenants can submit via this generic endpoint for now, OR admin must have a way to specify tenant.
        # Given the plan "Implement POST /api/payments (submit payment - tenant)", we'll focus on tenant.
        if not current_user.tenant:
             raise HTTPException(status_code=400, detail="Admin submission requires specifying tenant (not yet implemented in this simplified endpoint)")
        tenant_id = current_user.tenant.id

    # Check for duplicate payment for the same month
    existing_payment = db.query(models.RentPayment).filter(
        models.RentPayment.tenant_id == tenant_id,
        models.RentPayment.payment_month == payment.payment_month
    ).first()
    
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment for this month already exists")

    db_payment = models.RentPayment(
        tenant_id=tenant_id,
        **payment.model_dump()
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.get("/", response_model=List[schemas.RentPaymentResponse])
def read_payments(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = None,
    status: Optional[models.PaymentStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    query = db.query(models.RentPayment)
    
    if current_user.role == models.UserRole.TENANT.value:
        # Tenant can only see their own
        if not current_user.tenant:
            return []
        query = query.filter(models.RentPayment.tenant_id == current_user.tenant.id)
    elif tenant_id:
        # Admin can filter by tenant
        query = query.filter(models.RentPayment.tenant_id == tenant_id)
        
    if status:
        query = query.filter(models.RentPayment.status == status.value)
        
    payments = query.offset(skip).limit(limit).all()
    return payments

@router.get("/{payment_id}", response_model=schemas.RentPaymentResponse)
def read_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    payment = db.query(models.RentPayment).filter(models.RentPayment.id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    if current_user.role == models.UserRole.TENANT.value:
        if not current_user.tenant or payment.tenant_id != current_user.tenant.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this payment")
            
    return payment

@router.put("/{payment_id}/verify", response_model=schemas.RentPaymentResponse)
def verify_payment(
    payment_id: int,
    payment_update: schemas.PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    payment = db.query(models.RentPayment).filter(models.RentPayment.id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    if payment_update.status:
        payment.status = payment_update.status.value
    if payment_update.remarks:
        payment.remarks = payment_update.remarks
        
    db.commit()
    db.refresh(payment)
    return payment
