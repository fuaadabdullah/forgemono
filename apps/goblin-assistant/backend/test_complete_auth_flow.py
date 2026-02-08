import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import get_db
from models_base import User
from auth.policies import UserRole


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def test_register_user(client: TestClient, db_session: Session):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "testpass123",
            "name": "Test User",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "user_id" in data
    assert data["message"] == "User registered successfully"

    # Verify user was created in database
    user = db_session.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None
    assert user.name == "Test User"
    assert user.role == UserRole.USER.value
    assert user.password_hash is not None


def test_register_duplicate_email(client: TestClient):
    """Test registering with an email that already exists."""
    # First registration
    client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "testpass123"},
    )

    # Second registration with same email
    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "password": "differentpass"},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client: TestClient):
    """Test successful login."""
    # First register a user
    client.post(
        "/auth/register",
        json={"email": "loginuser@example.com", "password": "testpass123"},
    )

    # Now login
    response = client.post(
        "/auth/login",
        json={"email": "loginuser@example.com", "password": "testpass123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password."""
    # First register a user
    client.post(
        "/auth/register",
        json={"email": "wrongpass@example.com", "password": "correctpass"},
    )

    # Try to login with wrong password
    response = client.post(
        "/auth/login", json={"email": "wrongpass@example.com", "password": "wrongpass"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login", json={"email": "nonexistent@example.com", "password": "testpass"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_refresh_token_flow(client: TestClient):
    """Test complete token refresh flow."""
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "refreshtest@example.com", "password": "testpass123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "refreshtest@example.com", "password": "testpass123"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Refresh the access token
    refresh_response = client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient):
    """Test getting current user info."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "currentuser@example.com",
            "password": "testpass123",
            "name": "Current User",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "currentuser@example.com", "password": "testpass123"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Get current user info
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "currentuser@example.com"
    assert data["name"] == "Current User"
    assert data["role"] == UserRole.USER.value


if __name__ == "__main__":
    pytest.main([__file__])
