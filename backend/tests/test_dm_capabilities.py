"""Tests for DM capabilities - viewing and editing all player characters."""

import pytest
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use same test database as other tests
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


def create_user(username, email, is_dm=False):
    """Helper to create a user and return token."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "testpass123",
            "is_dm": is_dm,
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def create_character(token, name, character_class="Fighter"):
    """Helper to create a character."""
    response = client.post(
        "/api/v1/characters/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "race": "Human",
            "character_class": character_class,
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
    return response.json()


class TestDMAllCharacters:
    """Tests for the /characters/all endpoint (DM only)."""

    def test_dm_can_view_all_characters(self):
        """DM can view all characters from all players."""
        # Create a DM
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        # Create a player with a character
        player_token = create_user("player1", "player1@example.com", is_dm=False)
        player_char = create_character(player_token, "PlayerChar", "Wizard")

        # DM creates their own character
        dm_char = create_character(dm_token, "DMChar", "Rogue")

        # DM requests all characters
        response = client.get(
            "/api/v1/characters/all",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        characters = response.json()
        assert len(characters) == 2

        # Both characters should be visible
        names = [c["name"] for c in characters]
        assert "PlayerChar" in names
        assert "DMChar" in names

    def test_player_cannot_view_all_characters(self):
        """Non-DM players cannot access /characters/all endpoint."""
        # Create a player
        player_token = create_user("player1", "player1@example.com", is_dm=False)
        create_character(player_token, "PlayerChar")

        # Player tries to access all characters
        response = client.get(
            "/api/v1/characters/all",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert response.status_code == 403
        assert "Only the DM" in response.json()["detail"]

    def test_dm_sees_multiple_player_characters(self):
        """DM can see characters from multiple players."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        # Create multiple players with characters
        player1_token = create_user("player1", "player1@example.com")
        player2_token = create_user("player2", "player2@example.com")
        player3_token = create_user("player3", "player3@example.com")

        create_character(player1_token, "Fighter1", "Fighter")
        create_character(player2_token, "Wizard1", "Wizard")
        create_character(player3_token, "Cleric1", "Cleric")

        # DM requests all characters
        response = client.get(
            "/api/v1/characters/all",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        characters = response.json()
        assert len(characters) == 3


class TestDMEditCharacters:
    """Tests for DM editing player characters."""

    def test_dm_can_edit_player_character(self):
        """DM can edit any player's character."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        player_token = create_user("player1", "player1@example.com")
        char = create_character(player_token, "PlayerChar")

        # DM edits the player's character
        response = client.put(
            f"/api/v1/characters/{char['id']}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"name": "DM Renamed This"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "DM Renamed This"

    def test_player_cannot_edit_other_player_character(self):
        """Players cannot edit other players' characters."""
        player1_token = create_user("player1", "player1@example.com")
        player2_token = create_user("player2", "player2@example.com")
        char = create_character(player1_token, "Player1Char")

        # Player 2 tries to edit Player 1's character
        response = client.put(
            f"/api/v1/characters/{char['id']}",
            headers={"Authorization": f"Bearer {player2_token}"},
            json={"name": "Hacked Name"},
        )

        assert response.status_code == 403

    def test_dm_can_update_player_hp(self):
        """DM can update HP on any player's character."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        player_token = create_user("player1", "player1@example.com")
        char = create_character(player_token, "PlayerChar")

        # DM applies damage to player's character
        response = client.post(
            f"/api/v1/characters/{char['id']}/damage-healing",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"type": "damage", "amount": 5},
        )

        assert response.status_code == 200
        assert response.json()["current_hp"] == 7  # 12 - 5

    def test_dm_can_get_specific_player_character(self):
        """DM can view a specific player's character by ID."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        player_token = create_user("player1", "player1@example.com")
        char = create_character(player_token, "PlayerChar")

        # DM gets the player's character
        response = client.get(
            f"/api/v1/characters/{char['id']}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "PlayerChar"
