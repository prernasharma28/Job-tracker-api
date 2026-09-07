from fastapi import APIRouter, Depends, HTTPException, status

from ..database import SessionLocal
from ..models import UserDB
from ..schemas import UserCreate, UserResponse
from ..security import hash_password, verify_password

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

    if not existing_user or not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    return {
        "message": "Login Successful",
        "user": {
            "id": existing_user.id,
            "email": existing_user.email,
            "created_at": existing_user.created_at
        }
    }