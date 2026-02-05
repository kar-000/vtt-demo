"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "is_dm": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["is_dm"] is False


def test_register_duplicate_username():
    """Test that duplicate usernames are rejected."""
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "testpass123",
        },
    )

    # Try to register with same username
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login():
    """Test user login."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"


def test_login_wrong_password():
    """Test login with wrong password."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        },
    )

    # Try to login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


def test_create_character_with_valid_token():
    """Test creating a character with valid authentication."""
    # Register and get token
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    token = register_response.json()["access_token"]

    # Create character
    response = client.post(
        "/api/v1/characters/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Character",
            "race": "Human",
            "character_class": "Fighter",
            "level": 1,
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
            "armor_class": 16,
            "max_hp": 12,
            "current_hp": 12,
            "speed": 30,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Character"
    assert data["race"] == "Human"
    assert data["strength_modifier"] == 3  # (16 - 10) // 2


def test_create_character_without_token():
    """Test that creating a character without token fails."""
    response = client.post(
        "/api/v1/characters/",
        json={
            "name": "Test Character",
            "race": "Human",
            "character_class": "Fighter",
            "level": 1,
        },
    )
    assert response.status_code == 403  # No credentials provided


def test_get_current_user():
    """Test getting current user info."""
    # Register and get token
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "is_dm": True,
        },
    )
    token = register_response.json()["access_token"]

    # Get current user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["is_dm"] is True
