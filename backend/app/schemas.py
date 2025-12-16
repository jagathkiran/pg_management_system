from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List
from backend.app.models import UserRole, RoomType, PaymentStatus, MaintenancePriority, MaintenanceStatus, MaintenanceCategory

# Base Schemas (common attributes)
class UserBase(BaseModel):
    email: EmailStr

class RoomBase(BaseModel):
    room_number: str
    floor: int
    room_type: RoomType
    capacity: int
    monthly_rent: float

class TenantBase(BaseModel):
    full_name: str
    phone: str
    emergency_contact: str
    check_in_date: date
    check_out_date: Optional[date] = None
    deposit_amount: float = 0.0

class PaymentBase(BaseModel):
    amount: float
    payment_date: date
    payment_method: str = "Bank Transfer"
    transaction_id: str
    payment_month: date
    proof_image_path: Optional[str] = None

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    remarks: Optional[str] = None

class MaintenanceUpdate(BaseModel):
    status: Optional[MaintenanceStatus] = None
    resolution_notes: Optional[str] = None

class MaintenanceBase(BaseModel):
    category: MaintenanceCategory
    priority: MaintenancePriority
    description: str
    image_path: Optional[str] = None # Assuming path to uploaded image

# Create Schemas (for input)
class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.TENANT

class RoomCreate(RoomBase):
    pass

class TenantCreate(TenantBase):
    email: EmailStr
    room_id: Optional[int] = None

class PaymentCreate(PaymentBase):
    tenant_id: int # Tenant who made the payment

class MaintenanceCreate(MaintenanceBase):
    tenant_id: int

# Response Schemas (for output, includes IDs and created_at/updated_at)
class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Allow ORM models to be converted

class RoomResponse(RoomBase):
    id: int
    is_active: bool
    tenants: List["TenantResponseWithoutRelations"] = [] # Forward reference

    class Config:
        from_attributes = True

class TenantResponse(TenantBase):
    id: int
    user_id: int
    room_id: Optional[int] = None
    is_active: bool
    
    user: UserResponse # Nested user response
    room: Optional[RoomResponse] = None # Nested room response (can be None)
    payments: List["PaymentResponseWithoutRelations"] = []
    maintenance_requests: List["MaintenanceResponseWithoutRelations"] = []

    class Config:
        from_attributes = True

class RentPaymentResponse(PaymentBase):
    id: int
    tenant_id: int
    status: PaymentStatus
    proof_image_path: Optional[str] = None
    remarks: Optional[str] = None

    tenant: "TenantResponseWithoutRelations" # Nested tenant response

    class Config:
        from_attributes = True

class MaintenanceRequestResponse(MaintenanceBase):
    id: int
    tenant_id: int
    status: MaintenanceStatus
    request_date: datetime
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    tenant: "TenantResponseWithoutRelations" # Nested tenant response

    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Helper schemas to avoid circular dependencies and overly verbose nested responses
class TenantResponseWithoutRelations(TenantBase):
    id: int
    user_id: int
    room_id: Optional[int] = None
    is_active: bool
    class Config:
        from_attributes = True

class PaymentResponseWithoutRelations(PaymentBase):
    id: int
    tenant_id: int
    status: PaymentStatus
    proof_image_path: Optional[str] = None
    remarks: Optional[str] = None
    class Config:
        from_attributes = True

class MaintenanceResponseWithoutRelations(MaintenanceBase):
    id: int
    tenant_id: int
    status: MaintenanceStatus
    request_date: datetime
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    class Config:
        from_attributes = True

# Update Forward Refs for nested models
UserResponse.model_rebuild()
RoomResponse.model_rebuild()
TenantResponse.model_rebuild()
RentPaymentResponse.model_rebuild()
MaintenanceRequestResponse.model_rebuild()
