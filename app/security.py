from passlib.context import CryptContext

from jose import jwt

# Create a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash a password during registeration or password change
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify a password against a hashed password during login or authentication
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)