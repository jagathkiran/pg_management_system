import sys
import os
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import SessionLocal, engine, Base
from backend.app import models
from backend.app import schemas
from sqlalchemy.orm import Session

def test_models_and_schemas():
    print("Testing Database Models and Schemas...")
    
    # recreate tables for a clean slate (optional, but good for testing)
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Create a User
        print("\n1. Creating User...")
        user = models.User(
            email="test@example.com",
            hashed_password="fakehash123",
            role=models.UserRole.TENANT
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"   User created: ID={user.id}, Email={user.email}")
        
        # Validate with Schema
        user_schema = schemas.UserResponse.model_validate(user)
        print(f"   Schema Validation: Success! {user_schema.email}")

        # 2. Create a Room
        print("\n2. Creating Room...")
        room = models.Room(
            room_number="101",
            floor=1,
            room_type=models.RoomType.SINGLE,
            capacity=1,
            monthly_rent=500.0
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        print(f"   Room created: ID={room.id}, Number={room.room_number}")

        # Validate with Schema
        room_schema = schemas.RoomResponse.model_validate(room)
        print(f"   Schema Validation: Success! Room {room_schema.room_number}")

        # 3. Create a Tenant
        print("\n3. Creating Tenant...")
        tenant = models.Tenant(
            user_id=user.id,
            room_id=room.id,
            full_name="John Doe",
            phone="1234567890",
            emergency_contact="0987654321",
            check_in_date=date.today(),
            deposit_amount=1000.0
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"   Tenant created: ID={tenant.id}, Name={tenant.full_name}")
        
        # Validate with Schema
        tenant_schema = schemas.TenantResponse.model_validate(tenant)
        print(f"   Schema Validation: Success! Tenant linked to User {tenant_schema.user.id} and Room {tenant_schema.room.id}")

        # 4. Create a Payment
        print("\n4. Creating Payment...")
        payment = models.RentPayment(
            tenant_id=tenant.id,
            amount=500.0,
            payment_date=date.today(),
            payment_method="Bank Transfer",
            transaction_id="TXN123456",
            payment_month=date(2023, 10, 1),
            status=models.PaymentStatus.PENDING
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        print(f"   Payment created: ID={payment.id}, Amount={payment.amount}")

        # Validate with Schema
        payment_schema = schemas.RentPaymentResponse.model_validate(payment)
        print(f"   Schema Validation: Success! Payment for Tenant {payment_schema.tenant.full_name}")

        # 5. Create a Maintenance Request
        print("\n5. Creating Maintenance Request...")
        request = models.MaintenanceRequest(
            tenant_id=tenant.id,
            category=models.MaintenanceCategory.PLUMBING,
            priority=models.MaintenancePriority.HIGH,
            description="Leaky faucet",
            status=models.MaintenanceStatus.OPEN
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        print(f"   Request created: ID={request.id}, Desc={request.description}")

        # Validate with Schema
        request_schema = schemas.MaintenanceRequestResponse.model_validate(request)
        print(f"   Schema Validation: Success! Request status: {request_schema.status}")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup (optional - delete created data)
        # db.delete(request)
        # db.delete(payment)
        # db.delete(tenant)
        # db.delete(room)
        # db.delete(user)
        # db.commit()
        
        db.close()
        print("\nTest Complete.")

if __name__ == "__main__":
    test_models_and_schemas()
