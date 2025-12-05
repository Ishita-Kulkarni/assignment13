"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional, Literal


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")


class UserCreate(UserBase):
    """Schema for user registration/creation."""
    password: str = Field(..., min_length=8, max_length=100, description="Password (minimum 8 characters)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "password": "securepassword123"
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "securepassword123"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe_updated",
                "email": "john.updated@example.com"
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john.doe@example.com",
                "created_at": "2025-11-19T12:00:00",
                "updated_at": "2025-11-19T12:00:00",
                "is_active": True
            }
        }
    )


# Alias for UserRead (same as UserResponse)
UserRead = UserResponse


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )


class AuthResponse(BaseModel):
    """Schema for authentication response (login/register)."""
    message: str
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Login successful",
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john.doe@example.com",
                    "created_at": "2025-11-19T12:00:00",
                    "updated_at": "2025-11-19T12:00:00",
                    "is_active": True
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )


class Message(BaseModel):
    """Generic message response schema."""
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )


# ============================================
# Calculation Schemas
# ============================================

class CalculationBase(BaseModel):
    """Base calculation schema with common attributes."""
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: Literal["add", "subtract", "multiply", "divide"] = Field(
        ..., 
        description="Type of calculation operation"
    )

    @model_validator(mode='after')
    def validate_division_by_zero(self):
        """Prevent division by zero."""
        if self.type == 'divide' and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        return self


class CalculationCreate(CalculationBase):
    """Schema for creating a new calculation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "a": 10.5,
                "b": 5.2,
                "type": "add"
            }
        }
    )


class CalculationResponse(CalculationBase):
    """Schema for calculation response (includes computed result)."""
    id: int
    user_id: int
    result: float
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "a": 10.5,
                "b": 5.2,
                "type": "add",
                "result": 15.7,
                "created_at": "2025-11-27T12:00:00"
            }
        }
    )


# Alias for CalculationRead (same as CalculationResponse)
CalculationRead = CalculationResponse


class CalculationUpdate(BaseModel):
    """Schema for updating a calculation (optional fields)."""
    a: Optional[float] = Field(None, description="First operand")
    b: Optional[float] = Field(None, description="Second operand")
    type: Optional[Literal["add", "subtract", "multiply", "divide"]] = Field(
        None, 
        description="Type of calculation operation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "a": 20.0,
                "b": 10.0,
                "type": "multiply"
            }
        }
    )
