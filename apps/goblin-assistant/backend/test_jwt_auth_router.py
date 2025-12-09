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


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(email="test@example.com", role=UserRole.USER, token_version=1)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_endpoint(client: TestClient, test_user: User):
    """Test the login endpoint."""
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpass",  # Note: password verification not implemented yet
        },
    )

    # Should succeed since user exists (password check is TODO)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_user(client: TestClient):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login", json={"email": "nonexistent@example.com", "password": "testpass"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_refresh_token(client: TestClient, test_user: User):
    """Test token refresh endpoint."""
    # First login to get tokens
    login_response = client.post(
        "/auth/login", json={"email": test_user.email, "password": "testpass"}
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Now refresh the access token
    refresh_response = client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_invalid_token(client: TestClient):
    """Test refresh with invalid token."""
    response = client.post(
        "/auth/refresh", json={"refresh_token": "invalid.token.here"}
    )

    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]


def test_get_current_user(client: TestClient, test_user: User):
    """Test getting current user info."""
    # First login to get access token
    login_response = client.post(
        "/auth/login", json={"email": test_user.email, "password": "testpass"}
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Now get current user info
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role.value


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token"})

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
