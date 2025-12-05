"""
Simple script to test JWT authentication endpoints.
Run this after starting the application.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test user registration endpoint"""
    print("\n=== Testing /register endpoint ===")
    
    # Test data
    user_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "securepassword123"
    }
    
    response = requests.post(f"{BASE_URL}/users/register", json=user_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✓ Registration successful!")
        return response.json()
    else:
        print("✗ Registration failed!")
        return None


def test_login(username, password):
    """Test user login endpoint"""
    print("\n=== Testing /login endpoint ===")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✓ Login successful!")
        return response.json()
    else:
        print("✗ Login failed!")
        return None


def test_invalid_login():
    """Test login with invalid credentials"""
    print("\n=== Testing /login with invalid credentials ===")
    
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("✓ Correctly returned 401 Unauthorized!")
        return True
    else:
        print("✗ Should have returned 401!")
        return False


def test_protected_endpoint(token):
    """Test accessing a protected endpoint with JWT token"""
    print("\n=== Testing protected endpoint /users/me ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✓ Successfully accessed protected endpoint!")
        return True
    else:
        print("✗ Failed to access protected endpoint!")
        return False


def main():
    """Run all tests"""
    print("Starting JWT Authentication Tests...")
    print("Make sure the application is running on http://localhost:8000")
    
    # Test registration
    register_response = test_register()
    
    if register_response:
        token = register_response.get("access_token")
        username = register_response.get("user", {}).get("username")
        
        # Test login with the registered user
        test_login(username, "securepassword123")
        
        # Test invalid login
        test_invalid_login()
        
        # Test protected endpoint
        if token:
            test_protected_endpoint(token)
    
    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    main()
