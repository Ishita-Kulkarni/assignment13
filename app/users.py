"""
User CRUD operations and authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserLogin, UserUpdate, Message, Token, AuthResponse
from app.auth import hash_password, verify_password, create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, security
from app.logger_config import get_logger

logger = get_logger()

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP bearer token credentials
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
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
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and return JWT token.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    
    Returns:
    - **message**: Success message
    - **user**: User information
    - **access_token**: JWT access token for authentication
    - **token_type**: Token type (bearer)
    """
    logger.info(f"Registration attempt for username: {user_data.username}, email: {user_data.email}")
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"Registration failed: Username '{user_data.username}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"Registration failed: Email '{user_data.email}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token for the newly registered user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"User registered successfully: {new_user.username} (ID: {new_user.id})")
    return {
        "message": "Registration successful",
        "user": UserResponse.model_validate(new_user),
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=AuthResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return user information with access token.
    
    - **username**: Username or email
    - **password**: User password
    
    Returns:
    - **message**: Success message
    - **user**: User information
    - **access_token**: JWT access token for authentication
    - **token_type**: Token type (bearer)
    """
    logger.info(f"Login attempt for: {login_data.username}")
    
    # Try to find user by username or email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user:
        logger.warning(f"Login failed: User '{login_data.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        logger.warning(f"Login failed: Invalid password for user '{login_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        logger.warning(f"Login failed: User '{login_data.username}' is inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in successfully: {user.username} (ID: {user.id})")
    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user),
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user_dependency)):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    Format: Authorization: Bearer <token>
    
    Returns:
    - User information for the authenticated user
    """
    logger.info(f"Getting current user info: {current_user.username} (ID: {current_user.id})")
    return current_user


@router.get("", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all users with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    logger.info(f"Fetching users with skip={skip}, limit={limit}")
    users = db.query(User).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(users)} users")
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a specific user by ID.
    
    - **user_id**: User ID
    """
    logger.info(f"Fetching user with ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.warning(f"User not found: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User retrieved: {user.username} (ID: {user.id})")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Update user information.
    
    - **user_id**: User ID
    - **username**: New username (optional)
    - **email**: New email (optional)
    - **password**: New password (optional)
    """
    logger.info(f"Update attempt for user ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.warning(f"Update failed: User not found (ID: {user_id})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update username if provided
    if user_data.username:
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_user:
            logger.warning(f"Update failed: Username '{user_data.username}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_data.username
    
    # Update email if provided
    if user_data.email:
        existing_email = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_email:
            logger.warning(f"Update failed: Email '{user_data.email}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = user_data.email
    
    # Update password if provided
    if user_data.password:
        user.password_hash = hash_password(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated successfully: {user.username} (ID: {user.id})")
    return user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user by ID.
    
    - **user_id**: User ID
    """
    logger.info(f"Delete attempt for user ID: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.warning(f"Delete failed: User not found (ID: {user_id})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    logger.info(f"User deleted successfully: {username} (ID: {user_id})")
    return {"message": f"User '{username}' deleted successfully"}
