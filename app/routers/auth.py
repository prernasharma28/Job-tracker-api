from fastapi import APIRouter, Depends, HTTPException

from ..database import SessionLocal
from ..models import UserDB
from ..schemas import UserCreate, UserResponse, RefreshTokenRequest
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)


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


@router.post("/register", response_model=UserResponse, status_code=201)
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

    return new_user


@router.post("/login")
def login_user(user: UserCreate, db=Depends(get_db)):

    existing_user = db.query(UserDB).filter(
        UserDB.email == user.email
    ).first()

    if not existing_user or not verify_password(
        user.password,
        existing_user.password_hash
    ):
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

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_access_token(request: RefreshTokenRequest):

    payload = verify_refresh_token(
        request.refresh_token
    )

    new_access_token = create_access_token({
        "user_id": payload["user_id"],
        "email": payload["email"]
    })

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }