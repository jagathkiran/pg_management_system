from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from backend.app import database, models, schemas, auth
from backend.app.config import settings
from backend.app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != models.UserRole.ADMIN.value:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

async def get_current_tenant_user(current_user: models.User = Depends(get_current_active_user)):
    # Both tenants and admins should probably be able to access tenant routes, or maybe just tenants.
    # For now, let's assume this role check enforces that the user is a tenant or admin acting as tenant.
    # But strictly speaking, if it's "get_current_tenant_user", it might imply ONLY tenants.
    # However, usually admins have superuser access.
    # The plan says "get_current_tenant_user dependency".
    # Let's verify role is TENANT.
    if current_user.role != models.UserRole.TENANT.value and current_user.role != models.UserRole.ADMIN.value:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
