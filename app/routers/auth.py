import logging

from fastapi import APIRouter, Depends, HTTPException

from ..database import SessionLocal
from ..models import UserDB, RefreshTokenDB
from ..schemas import UserCreate, UserResponse, RefreshTokenRequest
from datetime import datetime, timedelta
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse, status_code=201, summary="Register a new user",
    description="Register a new user with an email and password.")
def register_user(user: UserCreate, db=Depends(get_db)):

    # Check if the user already exists
    existing_user = db.query(UserDB).filter(
        UserDB.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = UserDB(
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        "User registered: user_id=%s",
        new_user.id,
    )

    return new_user


@router.post("/login", summary="Login a user",
    description="Login a user with an email and password.")
def login_user(user: UserCreate, db=Depends(get_db)):

    existing_user = db.query(UserDB).filter(
        UserDB.email == user.email
    ).first()

    if not existing_user or not verify_password(
        user.password,
        existing_user.password_hash
    ):
        logger.warning(
            "Login failed: invalid credentials"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "user_id": existing_user.id,
        "email": existing_user.email
    })

    new_refresh_token = create_refresh_token({
        "user_id": existing_user.id,
        "email": existing_user.email
    })

    # Store the refresh token in the database
    refresh_token_record = RefreshTokenDB(
        user_id=existing_user.id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(refresh_token_record)
    db.commit()

    logger.info(
        "User logged in: user_id=%s",
        existing_user.id,
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", summary="Refresh access token",
    description="Refresh the access token using a valid refresh token.")
def refresh_access_token(request: RefreshTokenRequest, db=Depends(get_db)):

    payload = verify_refresh_token(request.refresh_token)

    refresh_token_record = db.query(RefreshTokenDB).filter(
        RefreshTokenDB.token == request.refresh_token
    ).first()

    if not refresh_token_record:
        raise HTTPException(
            status_code=401,
            detail="Refresh token not found"
        )

    if refresh_token_record.revoked:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has been revoked"
        )

    if refresh_token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired"
        )

    new_access_token = create_access_token({
        "user_id": payload["user_id"],
        "email": payload["email"]
    })

    logger.info(
        "Access token refreshed: user_id=%s",
        payload["user_id"],
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.post("/logout", summary="Logout a user",
    description="Logout a user and invalidate their refresh token.")
def logout_user(
    request: RefreshTokenRequest,
    db=Depends(get_db)
):
    refresh_token_record = db.query(RefreshTokenDB).filter(
        RefreshTokenDB.token == request.refresh_token
    ).first()

    if not refresh_token_record:
        raise HTTPException(
            status_code=401,
            detail="Refresh token not found"
        )

    if refresh_token_record.revoked:
        raise HTTPException(
            status_code=401,
            detail="Refresh token already revoked"
        )

    refresh_token_record.revoked = True
    db.commit()

    logger.info(
        "User logged out: user_id=%s",
        refresh_token_record.user_id,
    )

    return {
        "message": "Successfully logged out"
    }