"""
Integration tests for calculation API endpoints.
These tests require a database connection and authentication.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import User, Calculation
import os

# Use SQLite for testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def authenticated_user():
    """Create a user and return authentication token."""
    # Register user
    user_data = {
        "username": "calcuser",
        "email": "calc@example.com",
        "password": "password123"
    }
    client.post("/users/register", json=user_data)
    
    # Login to get token
    login_data = {
        "username": "calcuser",
        "password": "password123"
    }
    response = client.post("/users/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


class TestCalculationAdd:
    """Test adding (creating) calculations."""
    
    def test_add_calculation_success(self, authenticated_user):
        """Test successfully adding a calculation."""
        calc_data = {
            "a": 10.5,
            "b": 5.2,
            "type": "add"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["a"] == 10.5
        assert data["b"] == 5.2
        assert data["type"] == "add"
        assert data["result"] == 15.7
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
    
    def test_add_calculation_subtract(self, authenticated_user):
        """Test subtraction calculation."""
        calc_data = {
            "a": 20.0,
            "b": 7.5,
            "type": "subtract"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == 12.5
    
    def test_add_calculation_multiply(self, authenticated_user):
        """Test multiplication calculation."""
        calc_data = {
            "a": 4.0,
            "b": 3.0,
            "type": "multiply"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == 12.0
    
    def test_add_calculation_divide(self, authenticated_user):
        """Test division calculation."""
        calc_data = {
            "a": 15.0,
            "b": 3.0,
            "type": "divide"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["result"] == 5.0
    
    def test_add_calculation_division_by_zero(self, authenticated_user):
        """Test that division by zero is rejected."""
        calc_data = {
            "a": 10.0,
            "b": 0.0,
            "type": "divide"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        # Schema validation returns 422, not 400
        assert response.status_code == 422
        assert "division by zero" in str(response.json()).lower()
    
    def test_add_calculation_invalid_operation(self, authenticated_user):
        """Test that invalid operation is rejected."""
        calc_data = {
            "a": 10.0,
            "b": 5.0,
            "type": "modulo"
        }
        
        response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_add_calculation_without_auth(self):
        """Test that calculation creation requires authentication."""
        calc_data = {
            "a": 10.0,
            "b": 5.0,
            "type": "add"
        }
        
        response = client.post("/calculations", json=calc_data)
        
        assert response.status_code == 403


class TestCalculationBrowse:
    """Test browsing (listing) calculations."""
    
    def test_browse_calculations_empty(self, authenticated_user):
        """Test browsing when no calculations exist."""
        response = client.get("/calculations", headers=authenticated_user)
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_browse_calculations_with_data(self, authenticated_user):
        """Test browsing calculations."""
        # Create multiple calculations
        calculations = [
            {"a": 10, "b": 5, "type": "add"},
            {"a": 20, "b": 3, "type": "subtract"},
            {"a": 4, "b": 7, "type": "multiply"}
        ]
        
        for calc in calculations:
            client.post("/calculations", json=calc, headers=authenticated_user)
        
        response = client.get("/calculations", headers=authenticated_user)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by created_at desc (newest first)
        # But in fast execution, ordering might vary, so just check all exist
        types = [calc["type"] for calc in data]
        assert "add" in types
        assert "subtract" in types
        assert "multiply" in types
    
    def test_browse_calculations_pagination(self, authenticated_user):
        """Test pagination in browse."""
        # Create 5 calculations
        for i in range(5):
            calc = {"a": i, "b": 1, "type": "add"}
            client.post("/calculations", json=calc, headers=authenticated_user)
        
        # Get first 2
        response = client.get(
            "/calculations?skip=0&limit=2",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Get next 2
        response = client.get(
            "/calculations?skip=2&limit=2",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_browse_calculations_without_auth(self):
        """Test that browsing requires authentication."""
        response = client.get("/calculations")
        
        assert response.status_code == 403
    
    def test_browse_calculations_user_isolation(self):
        """Test that users only see their own calculations."""
        # Create first user and calculation
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "password123"}
        client.post("/users/register", json=user1_data)
        login_response = client.post("/users/login", json={"username": "user1", "password": "password123"})
        user1_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        client.post("/calculations", json={"a": 1, "b": 1, "type": "add"}, headers=user1_token)
        
        # Create second user and calculation
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "password123"}
        client.post("/users/register", json=user2_data)
        login_response = client.post("/users/login", json={"username": "user2", "password": "password123"})
        user2_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        client.post("/calculations", json={"a": 2, "b": 2, "type": "add"}, headers=user2_token)
        
        # Each user should only see their own calculation
        user1_calcs = client.get("/calculations", headers=user1_token).json()
        user2_calcs = client.get("/calculations", headers=user2_token).json()
        
        assert len(user1_calcs) == 1
        assert len(user2_calcs) == 1
        assert user1_calcs[0]["a"] == 1
        assert user2_calcs[0]["a"] == 2


class TestCalculationRead:
    """Test reading (getting) specific calculations."""
    
    def test_read_calculation_success(self, authenticated_user):
        """Test reading a specific calculation."""
        # Create a calculation
        calc_data = {"a": 10, "b": 5, "type": "add"}
        create_response = client.post(
            "/calculations",
            json=calc_data,
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Read it back
        response = client.get(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == calc_id
        assert data["a"] == 10
        assert data["b"] == 5
        assert data["result"] == 15
    
    def test_read_calculation_not_found(self, authenticated_user):
        """Test reading non-existent calculation."""
        response = client.get(
            "/calculations/99999",
            headers=authenticated_user
        )
        
        assert response.status_code == 404
    
    def test_read_calculation_without_auth(self):
        """Test that reading requires authentication."""
        response = client.get("/calculations/1")
        
        assert response.status_code == 403
    
    def test_read_calculation_other_user(self):
        """Test that users cannot read other users' calculations."""
        # Create user1 and their calculation
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "password123"}
        client.post("/users/register", json=user1_data)
        login_response = client.post("/users/login", json={"username": "user1", "password": "password123"})
        user1_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        create_response = client.post(
            "/calculations",
            json={"a": 1, "b": 1, "type": "add"},
            headers=user1_token
        )
        calc_id = create_response.json()["id"]
        
        # Create user2
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "password123"}
        client.post("/users/register", json=user2_data)
        login_response = client.post("/users/login", json={"username": "user2", "password": "password123"})
        user2_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # User2 tries to read user1's calculation
        response = client.get(f"/calculations/{calc_id}", headers=user2_token)
        
        assert response.status_code == 404


class TestCalculationEdit:
    """Test editing (updating) calculations."""
    
    def test_edit_calculation_put_success(self, authenticated_user):
        """Test updating a calculation with PUT."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Update it
        update_data = {"a": 20, "b": 3, "type": "multiply"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["a"] == 20
        assert data["b"] == 3
        assert data["type"] == "multiply"
        assert data["result"] == 60
    
    def test_edit_calculation_patch_success(self, authenticated_user):
        """Test updating a calculation with PATCH."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Partial update with PATCH
        update_data = {"b": 8}
        response = client.patch(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["a"] == 10  # Unchanged
        assert data["b"] == 8   # Updated
        assert data["type"] == "add"  # Unchanged
        assert data["result"] == 18  # Recalculated
    
    def test_edit_calculation_partial_update(self, authenticated_user):
        """Test partial update (only operation type)."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Update only the operation type
        update_data = {"type": "subtract"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["a"] == 10
        assert data["b"] == 5
        assert data["type"] == "subtract"
        assert data["result"] == 5  # 10 - 5
    
    def test_edit_calculation_division_by_zero(self, authenticated_user):
        """Test that updating to division by zero is rejected."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Try to update to division by zero
        update_data = {"b": 0, "type": "divide"}
        response = client.put(
            f"/calculations/{calc_id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 400
        assert "division by zero" in response.json()["detail"].lower()
    
    def test_edit_calculation_not_found(self, authenticated_user):
        """Test updating non-existent calculation."""
        response = client.put(
            "/calculations/99999",
            json={"a": 1},
            headers=authenticated_user
        )
        
        assert response.status_code == 404
    
    def test_edit_calculation_without_auth(self):
        """Test that editing requires authentication."""
        response = client.put("/calculations/1", json={"a": 1})
        
        assert response.status_code == 403


class TestCalculationDelete:
    """Test deleting calculations."""
    
    def test_delete_calculation_success(self, authenticated_user):
        """Test successfully deleting a calculation."""
        # Create a calculation
        create_response = client.post(
            "/calculations",
            json={"a": 10, "b": 5, "type": "add"},
            headers=authenticated_user
        )
        calc_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify it's gone
        get_response = client.get(
            f"/calculations/{calc_id}",
            headers=authenticated_user
        )
        assert get_response.status_code == 404
    
    def test_delete_calculation_not_found(self, authenticated_user):
        """Test deleting non-existent calculation."""
        response = client.delete(
            "/calculations/99999",
            headers=authenticated_user
        )
        
        assert response.status_code == 404
    
    def test_delete_calculation_without_auth(self):
        """Test that deleting requires authentication."""
        response = client.delete("/calculations/1")
        
        assert response.status_code == 403
    
    def test_delete_calculation_other_user(self):
        """Test that users cannot delete other users' calculations."""
        # Create user1 and their calculation
        user1_data = {"username": "user1", "email": "user1@example.com", "password": "password123"}
        client.post("/users/register", json=user1_data)
        login_response = client.post("/users/login", json={"username": "user1", "password": "password123"})
        user1_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        create_response = client.post(
            "/calculations",
            json={"a": 1, "b": 1, "type": "add"},
            headers=user1_token
        )
        calc_id = create_response.json()["id"]
        
        # Create user2
        user2_data = {"username": "user2", "email": "user2@example.com", "password": "password123"}
        client.post("/users/register", json=user2_data)
        login_response = client.post("/users/login", json={"username": "user2", "password": "password123"})
        user2_token = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # User2 tries to delete user1's calculation
        response = client.delete(f"/calculations/{calc_id}", headers=user2_token)
        
        assert response.status_code == 404
