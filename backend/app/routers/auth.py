from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app import database, models, schemas, auth, dependencies
from backend.app.config import settings

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

@router.post("/login", response_model=schemas.Token)
async def login(login_data: schemas.UserLogin, db: Session = Depends(dependencies.get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    return {"message": "Logout successful"}

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(dependencies.get_current_active_user)):
    return current_user
