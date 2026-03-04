from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, LoginRequest, UserCreate, UserResponse
from app.core import security
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Any:
    """
    Registration is disabled for public. 
    Only Admin can add employees via User Management.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled. Please contact your administrator."
    )

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    login_data: LoginRequest = None
) -> Any:
    """
    Get access token for login with platform check.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Platform Access Control
    # Web Admin can only login on 'web'
    # Mobile App user can only login on 'mobile'
    # Superuser can login everywhere
    if not user.is_superuser:
        if login_data.client_platform == "web" and user.user_type != "WEB_ADMIN":
            raise HTTPException(
                status_code=403, 
                detail="This account is only authorized for Mobile App access."
            )
        if login_data.client_platform == "mobile" and user.user_type != "MOBILE_APP":
            raise HTTPException(
                status_code=403, 
                detail="This account is only authorized for Web Admin access."
            )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "user": user
    }
