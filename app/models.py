from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from .database import Base

class ApplicationDB(Base): # SQLAlchemy model for the applications table
    __tablename__ = "applications"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Foreign key to the users table
    id = Column(Integer, primary_key=True, index=True) # Every application will have a unique ID
    company = Column(String)
    role = Column(String)
    location = Column(String, nullable=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class UserDB(Base): # SQLAlchemy model for the users table
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RefreshTokenDB(Base): # SQLAlchemy model for the refresh_tokens table
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
