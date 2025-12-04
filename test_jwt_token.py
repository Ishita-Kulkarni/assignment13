"""
Quick test script to verify JWT token functionality.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_jwt_workflow():
    """Test the complete JWT authentication workflow."""
    
    # 1. Register a new user
    print("1. Registering a new user...")
    register_data = {
        "username": "testjwt",
        "email": "testjwt@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/register", json=register_data)
        print(f"   Registration Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   User created: {response.json()['username']}")
        elif response.status_code == 400:
            print("   User already exists, continuing with login...")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 2. Login and get JWT token
    print("\n2. Logging in to get JWT token...")
    login_data = {
        "username": "testjwt",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/login", json=login_data)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   ✓ Login successful!")
            print(f"   ✓ User: {data['user']['username']}")
            print(f"   ✓ Token received: {token[:50]}...")
            print(f"   ✓ Token type: {data.get('token_type')}")
        else:
            print(f"   Error: {response.json()}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # 3. Use token to access protected endpoint
    print("\n3. Accessing /users/me with token...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✓ Authentication successful!")
            print(f"   ✓ Current user: {user_data['username']}")
            print(f"   ✓ Email: {user_data['email']}")
        else:
            print(f"   Error: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Try to access without token (should fail)
    print("\n4. Trying to access /users/me without token...")
    try:
        response = requests.get(f"{BASE_URL}/users/me")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 403 or response.status_code == 401:
            print(f"   ✓ Correctly rejected unauthorized access!")
        else:
            print(f"   ⚠ Expected 401/403 but got {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ JWT Token workflow test completed!")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing JWT Token Implementation")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:8000")
    print("Start it with: uvicorn app.main:app --reload")
    print("\n" + "=" * 60 + "\n")
    
    test_jwt_workflow()
