# JWT Authentication Documentation

## Overview

This application implements JWT (JSON Web Token) based authentication for user registration and login. The authentication system provides secure password hashing using bcrypt and token-based authentication.

## Endpoints

### 1. User Registration - `/users/register`

**Method:** `POST`

**Description:** Register a new user account and receive a JWT token immediately upon successful registration.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Validation Rules:**
- `username`: 3-50 characters, must be unique
- `email`: Valid email format, must be unique
- `password`: Minimum 8 characters

**Success Response (201 Created):**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "created_at": "2025-12-04T12:00:00",
    "updated_at": "2025-12-04T12:00:00",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- **400 Bad Request** - Username or email already exists
  ```json
  {
    "detail": "Username already registered"
  }
  ```
  or
  ```json
  {
    "detail": "Email already registered"
  }
  ```

- **422 Unprocessable Entity** - Validation error (invalid format)
  ```json
  {
    "detail": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
  ```

**Implementation Details:**
- Passwords are hashed using bcrypt before storage
- Duplicate username/email checks are performed before registration
- JWT token is automatically generated and returned
- Token expiration time is configurable (default: 30 minutes)

---

### 2. User Login - `/users/login`

**Method:** `POST`

**Description:** Authenticate a user with username/email and password, returning a JWT token on success.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword123"
}
```

**Note:** The `username` field accepts either a username or email address.

**Success Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "created_at": "2025-12-04T12:00:00",
    "updated_at": "2025-12-04T12:00:00",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid credentials
  ```json
  {
    "detail": "Invalid username or password"
  }
  ```

- **403 Forbidden** - User account is inactive
  ```json
  {
    "detail": "User account is inactive"
  }
  ```

**Implementation Details:**
- Accepts both username and email for login
- Password verification using bcrypt
- Returns 401 for both non-existent users and wrong passwords (security best practice)
- Checks if user account is active before issuing token

---

## Using JWT Tokens

### Token Format

The JWT token follows the standard JWT format with three parts separated by dots:
```
header.payload.signature
```

Example:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzMzMzI1NjAwfQ.signature
```

### Token Payload

The token contains the following claims:
- `sub`: Username (subject)
- `exp`: Expiration timestamp (Unix timestamp)

### Using Tokens in Requests

Include the JWT token in the `Authorization` header for protected endpoints:

```http
GET /users/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Example with cURL

**Register:**
```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john.doe@example.com",
    "password": "securepassword123"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

**Access Protected Endpoint:**
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Example with Python (requests)

```python
import requests

# Register
response = requests.post(
    "http://localhost:8000/users/register",
    json={
        "username": "johndoe",
        "email": "john.doe@example.com",
        "password": "securepassword123"
    }
)
data = response.json()
token = data["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
user_info = requests.get(
    "http://localhost:8000/users/me",
    headers=headers
)
print(user_info.json())
```

### Example with JavaScript (fetch)

```javascript
// Register
const registerResponse = await fetch('http://localhost:8000/users/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'johndoe',
    email: 'john.doe@example.com',
    password: 'securepassword123'
  })
});

const data = await registerResponse.json();
const token = data.access_token;

// Use token for authenticated requests
const userResponse = await fetch('http://localhost:8000/users/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const userInfo = await userResponse.json();
console.log(userInfo);
```

---

## Security Configuration

### Environment Variables

Configure these in your `.env` file:

```env
# Security Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important:** Generate a strong secret key for production:
```bash
openssl rand -hex 32
```

### Password Requirements

- Minimum 8 characters
- Passwords are hashed using bcrypt with automatic salt generation
- Original passwords are never stored

### Token Expiration

- Default: 30 minutes
- Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable
- Expired tokens will result in 401 Unauthorized responses

---

## Testing

Run the included test script to verify authentication endpoints:

```bash
python test_auth_endpoints.py
```

The script tests:
- User registration with JWT token generation
- Successful login with valid credentials
- Failed login with invalid credentials (401 response)
- Accessing protected endpoints with JWT token

---

## Error Handling

All endpoints follow consistent error response formats:

### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

### Authentication Errors (401)
```json
{
  "detail": "Could not validate credentials"
}
```

### Business Logic Errors (400, 403, etc.)
```json
{
  "detail": "Human-readable error message"
}
```

---

## Protected Endpoints

Any endpoint that requires authentication should use the `get_current_user_dependency`:

```python
from app.users import get_current_user_dependency

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user_dependency)):
    return {"message": f"Hello {current_user.username}"}
```

This dependency:
- Validates the JWT token
- Extracts the user from the database
- Returns 401 if token is invalid or user not found
- Provides the authenticated user object to the endpoint
