"""
Authentication utilities for password hashing and verification.
"""
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

# Configure password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security scheme for bearer token
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> print(hashed)
        $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Alias for hash_password for backward compatibility.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return hash_password(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional token expiration time delta
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload as dictionary, or None if invalid
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        user123
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = None
):
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP bearer token credentials
        db: Database session (injected by FastAPI)
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
        
    Example:
        @app.get("/protected")
        async def protected_route(current_user = Depends(get_current_user)):
            return {"user": current_user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # If db is provided, fetch the user from database
    if db is not None:
        from app.models import User
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        return user
    
    # Return just the username if no db session
    return {"username": username}

