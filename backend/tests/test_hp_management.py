"""Tests for HP management endpoints."""

import pytest
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


def create_user_and_character():
    """Helper to create a test user and character."""
    # Register user
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
    char_response = client.post(
        "/api/v1/characters/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Character",
            "race": "Human",
            "character_class": "Fighter",
            "level": 5,
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
            "armor_class": 16,
            "max_hp": 40,
            "current_hp": 40,
            "temp_hp": 0,
            "speed": 30,
        },
    )
    character = char_response.json()
    return token, character


def test_update_hp_directly():
    """Test updating HP using PATCH endpoint."""
    token, character = create_user_and_character()

    # Update HP
    response = client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_hp": 25, "temp_hp": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 25
    assert data["temp_hp"] == 5


def test_update_hp_cannot_exceed_max():
    """Test that current HP cannot exceed max HP."""
    token, character = create_user_and_character()

    # Try to set HP above max
    response = client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_hp": 999},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == character["max_hp"]  # Capped at max


def test_apply_damage():
    """Test applying damage to a character."""
    token, character = create_user_and_character()

    # Apply 15 damage
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 15},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 25  # 40 - 15


def test_apply_healing():
    """Test applying healing to a character."""
    token, character = create_user_and_character()

    # First take damage
    client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 20},
    )

    # Now heal
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "healing", "amount": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 30  # (40 - 20) + 10


def test_healing_cannot_exceed_max_hp():
    """Test that healing cannot exceed max HP."""
    token, character = create_user_and_character()

    # Take damage
    client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 10},
    )

    # Heal more than needed
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "healing", "amount": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == character["max_hp"]


def test_damage_depletes_temp_hp_first():
    """Test that damage is applied to temp HP before current HP."""
    token, character = create_user_and_character()

    # Add temp HP
    client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"temp_hp": 10},
    )

    # Apply 5 damage (should only affect temp HP)
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temp_hp"] == 5  # 10 - 5
    assert data["current_hp"] == 40  # Unchanged


def test_damage_overflow_from_temp_to_current_hp():
    """Test that excess damage overflows from temp HP to current HP."""
    token, character = create_user_and_character()

    # Add temp HP
    client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"temp_hp": 10},
    )

    # Apply 15 damage (10 to temp, 5 to current)
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 15},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temp_hp"] == 0
    assert data["current_hp"] == 35  # 40 - 5


def test_damage_cannot_reduce_hp_below_zero():
    """Test that damage cannot reduce HP below 0."""
    token, character = create_user_and_character()

    # Apply massive damage
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 999},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 0  # Cannot go below 0


def test_death_saves_tracking():
    """Test that death saves can be tracked when at 0 HP."""
    token, character = create_user_and_character()

    # First reduce to 0 HP
    client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 999},
    )

    # Now update death saves
    response = client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"death_saves": {"successes": 2, "failures": 1}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 0
    assert data["death_saves"]["successes"] == 2
    assert data["death_saves"]["failures"] == 1


def test_death_saves_reset_on_healing():
    """Test that death saves reset when HP is restored above 0."""
    token, character = create_user_and_character()

    # Reduce to 0 HP and set death saves
    client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 999},
    )
    client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"death_saves": {"successes": 2, "failures": 1}},
    )

    # Heal back above 0
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "healing", "amount": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 10
    assert data["death_saves"]["successes"] == 0
    assert data["death_saves"]["failures"] == 0


def test_death_saves_reset_on_direct_hp_update():
    """Test that death saves reset when HP is directly set above 0."""
    token, character = create_user_and_character()

    # Reduce to 0 HP and set death saves
    client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "damage", "amount": 999},
    )
    client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"death_saves": {"successes": 1, "failures": 2}},
    )

    # Directly set HP above 0
    response = client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_hp": 15},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 15
    assert data["death_saves"]["successes"] == 0
    assert data["death_saves"]["failures"] == 0


def test_hp_update_requires_authentication():
    """Test that HP updates require authentication."""
    _, character = create_user_and_character()

    # Try to update without token
    response = client.patch(
        f"/api/v1/characters/{character['id']}/hp",
        json={"current_hp": 10},
    )
    assert response.status_code == 401


def test_damage_healing_requires_authentication():
    """Test that damage/healing requires authentication."""
    _, character = create_user_and_character()

    # Try to apply damage without token
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        json={"type": "damage", "amount": 10},
    )
    assert response.status_code == 401


def test_cannot_modify_other_users_character():
    """Test that users cannot modify other users' characters."""
    token1, character1 = create_user_and_character()

    # Create second user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "testpass123",
        },
    )
    token2 = register_response.json()["access_token"]

    # Try to modify first user's character with second user's token
    response = client.patch(
        f"/api/v1/characters/{character1['id']}/hp",
        headers={"Authorization": f"Bearer {token2}"},
        json={"current_hp": 1},
    )
    assert response.status_code == 403


def test_dm_can_modify_any_character():
    """Test that DMs can modify any character."""
    token1, character1 = create_user_and_character()

    # Create DM user
    dm_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "dmuser",
            "email": "dm@example.com",
            "password": "testpass123",
            "is_dm": True,
        },
    )
    dm_token = dm_response.json()["access_token"]

    # DM should be able to modify player's character
    response = client.patch(
        f"/api/v1/characters/{character1['id']}/hp",
        headers={"Authorization": f"Bearer {dm_token}"},
        json={"current_hp": 20},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_hp"] == 20


def test_invalid_damage_healing_type():
    """Test that invalid damage/healing type is rejected."""
    token, character = create_user_and_character()

    # Try invalid type
    response = client.post(
        f"/api/v1/characters/{character['id']}/damage-healing",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "invalid", "amount": 10},
    )
    assert response.status_code == 400
    assert "must be 'damage' or 'healing'" in response.json()["detail"]
