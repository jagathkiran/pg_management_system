from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base
import enum

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TENANT = "tenant"

class RoomType(str, enum.Enum):
    SINGLE = "Single"
    DOUBLE = "Double"
    TRIPLE = "Triple"

class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"

class MaintenancePriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class MaintenanceStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class MaintenanceCategory(str, enum.Enum):
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    FURNITURE = "Furniture"
    OTHER = "Other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.TENANT.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="user", uselist=False)

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, index=True)
    floor = Column(Integer)
    room_type = Column(String) 
    capacity = Column(Integer)
    monthly_rent = Column(Float)
    is_active = Column(Boolean, default=True)

    tenants = relationship("Tenant", back_populates="room")

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    full_name = Column(String)
    phone = Column(String)
    emergency_contact = Column(String)
    check_in_date = Column(Date)
    check_out_date = Column(Date, nullable=True)
    deposit_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="tenant")
    room = relationship("Room", back_populates="tenants")
    payments = relationship("RentPayment", back_populates="tenant")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="tenant")

class RentPayment(Base):
    __tablename__ = "rent_payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    amount = Column(Float)
    payment_date = Column(Date)
    payment_method = Column(String)
    transaction_id = Column(String)
    payment_month = Column(Date) # First day of the month being paid
    status = Column(String, default=PaymentStatus.PENDING.value)
    proof_image_path = Column(String, nullable=True)
    remarks = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="payments")

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    category = Column(String)
    priority = Column(String)
    description = Column(String)
    status = Column(String, default=MaintenanceStatus.OPEN.value)
    request_date = Column(DateTime(timezone=True), server_default=func.now())
    resolved_date = Column(DateTime(timezone=True), nullable=True)
    image_path = Column(String, nullable=True)
    resolution_notes = Column(String, nullable=True)

    tenant = relationship("Tenant", back_populates="maintenance_requests")
