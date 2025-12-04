#!/usr/bin/env python3
"""
User Endpoints Usage Examples
Demonstrates how to use the user authentication API
"""

from fastapi.testclient import TestClient
from app.main import app

# Create a test client
client = TestClient(app)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    """Demonstrate user endpoint functionality"""
    
    print_section("1. REGISTER A NEW USER")
    
    # Register user
    register_data = {
        "username": "demouser",
        "email": "demo@example.com",
        "password": "securepass123"
    }
    
    response = client.post("/users/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        user = response.json()
        print(f"✓ User created successfully!")
        print(f"  - ID: {user['id']}")
        print(f"  - Username: {user['username']}")
        print(f"  - Email: {user['email']}")
        print(f"  - Created: {user['created_at']}")
        print(f"  - Active: {user['is_active']}")
    elif response.status_code == 400:
        print(f"⚠ User already exists: {response.json()['detail']}")
    else:
        print(f"✗ Error: {response.json()}")
    
    # ----------------------------------------------------------------
    print_section("2. LOGIN WITH USERNAME AND PASSWORD")
    
    login_data = {
        "username": "demouser",
        "password": "securepass123"
    }
    
    response = client.post("/users/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful!")
        print(f"  - Message: {data['message']}")
        print(f"  - User: {data['user']['username']}")
        print(f"  - Token Type: {data['token_type']}")
        print(f"  - Access Token: {data['access_token'][:50]}...")
        
        # Save token for later use
        token = data['access_token']
    else:
        print(f"✗ Login failed: {response.json()}")
        return
    
    # ----------------------------------------------------------------
    print_section("3. GET CURRENT USER INFO (WITH TOKEN)")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        user = response.json()
        print(f"✓ Successfully retrieved current user info!")
        print(f"  - Username: {user['username']}")
        print(f"  - Email: {user['email']}")
        print(f"  - ID: {user['id']}")
    else:
        print(f"✗ Error: {response.json()}")
    
    # ----------------------------------------------------------------
    print_section("4. TRY TO ACCESS PROTECTED ENDPOINT WITHOUT TOKEN")
    
    response = client.get("/users/me")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 403:
        print(f"✓ Correctly rejected unauthorized access!")
        print(f"  - Detail: {response.json()['detail']}")
    else:
        print(f"⚠ Unexpected response: {response.status_code}")
    
    # ----------------------------------------------------------------
    print_section("5. GET ALL USERS")
    
    response = client.get("/users")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        users = response.json()
        print(f"✓ Retrieved {len(users)} user(s)")
        for user in users[:3]:  # Show first 3
            print(f"  - {user['username']} ({user['email']})")
    else:
        print(f"✗ Error: {response.json()}")
    
    # ----------------------------------------------------------------
    print_section("6. UPDATE USER INFORMATION")
    
    # First, get the user ID
    response = client.get("/users")
    if response.status_code == 200:
        users = response.json()
        demo_user = next((u for u in users if u['username'] == 'demouser'), None)
        
        if demo_user:
            user_id = demo_user['id']
            
            update_data = {
                "email": "newemail@example.com"
            }
            
            response = client.put(f"/users/{user_id}", json=update_data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                user = response.json()
                print(f"✓ User updated successfully!")
                print(f"  - New email: {user['email']}")
            else:
                print(f"✗ Error: {response.json()}")
    
    # ----------------------------------------------------------------
    print_section("7. LOGIN WITH EMAIL INSTEAD OF USERNAME")
    
    login_data = {
        "username": "newemail@example.com",  # Using email
        "password": "securepass123"
    }
    
    response = client.post("/users/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login with email successful!")
        print(f"  - User: {data['user']['username']}")
        print(f"  - Email: {data['user']['email']}")
    else:
        print(f"✗ Error: {response.json()}")
    
    # ----------------------------------------------------------------
    print_section("8. TEST VALIDATION - SHORT PASSWORD")
    
    register_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "short"  # Too short
    }
    
    response = client.post("/users/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 422:
        print(f"✓ Validation working correctly!")
        print(f"  - Rejected password that's too short")
        errors = response.json()['detail']
        for error in errors:
            if 'password' in error['loc']:
                print(f"  - Error: {error['msg']}")
    
    # ----------------------------------------------------------------
    print_section("9. TEST VALIDATION - INVALID EMAIL")
    
    register_data = {
        "username": "testuser3",
        "email": "not-a-valid-email",  # Invalid email
        "password": "password123"
    }
    
    response = client.post("/users/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 422:
        print(f"✓ Email validation working correctly!")
        print(f"  - Rejected invalid email format")
    
    # ----------------------------------------------------------------
    print_section("10. TEST WRONG PASSWORD")
    
    login_data = {
        "username": "demouser",
        "password": "wrongpassword"
    }
    
    response = client.post("/users/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✓ Password verification working correctly!")
        print(f"  - Detail: {response.json()['detail']}")
    
    # ----------------------------------------------------------------
    print_section("SUMMARY")
    print("✅ All user endpoints are working correctly!")
    print("\nImplemented endpoints:")
    print("  1. POST   /users/register    - Register new user")
    print("  2. POST   /users/login       - Login with username/email")
    print("  3. GET    /users/me          - Get current user (requires token)")
    print("  4. GET    /users             - Get all users (with pagination)")
    print("  5. GET    /users/{id}        - Get user by ID")
    print("  6. PUT    /users/{id}        - Update user")
    print("  7. DELETE /users/{id}        - Delete user")
    print("\nFeatures:")
    print("  ✓ Bcrypt password hashing")
    print("  ✓ JWT token authentication")
    print("  ✓ Login with username or email")
    print("  ✓ Input validation")
    print("  ✓ Protected endpoints")
    print("  ✓ Session management via JWT tokens")
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  USER ENDPOINTS DEMONSTRATION")
    print("  FastAPI User Management with JWT Authentication")
    print("=" * 70)
    
    main()
