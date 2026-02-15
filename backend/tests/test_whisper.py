"""Tests for whisper/secret roll functionality."""

import pytest
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_user(username, email, is_dm=False):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "testpass123",
            "is_dm": is_dm,
        },
    )
    return response.json()["access_token"]


def create_character(token, name):
    response = client.post(
        "/api/v1/characters/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "race": "Human",
            "character_class": "Fighter",
            "level": 1,
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
            "armor_class": 10,
            "max_hp": 10,
            "current_hp": 10,
            "temp_hp": 0,
            "speed": 30,
        },
    )
    return response.json()


def create_campaign(dm_id):
    from app.models.campaign import Campaign

    db = TestingSessionLocal()
    campaign = Campaign(id=1, name="Test Campaign", dm_id=dm_id, maps=[], settings={})
    db.add(campaign)
    db.commit()
    db.close()


class TestWhisperDiceRolls:
    """Test whisper routing for dice rolls."""

    def test_public_roll_broadcasts_to_all(self):
        """A roll without whisper_to should be broadcast to all."""
        dm_token = create_user("dm_w1", "dm_w1@test.com", is_dm=True)
        create_character(dm_token, "DM Char")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "DM Char",
                        "dice_type": 20,
                        "num_dice": 1,
                        "modifier": 0,
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "dice_roll_result"
            assert response["data"]["whisper_to"] is None

    def test_whisper_to_dm_includes_whisper_field(self):
        """A whispered roll should include whisper_to in the result."""
        dm_token = create_user("dm_w2", "dm_w2@test.com", is_dm=True)
        create_character(dm_token, "DM Char")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "DM Char",
                        "dice_type": 20,
                        "num_dice": 1,
                        "modifier": 0,
                        "whisper_to": "dm",
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "dice_roll_result"
            assert response["data"]["whisper_to"] == "dm"

    def test_whisper_to_dm_from_player(self):
        """Player whisper to DM: both DM and player should receive the roll."""
        dm_token = create_user("dm_w3", "dm_w3@test.com", is_dm=True)
        player_token = create_user("player_w3", "p_w3@test.com", is_dm=False)
        create_character(player_token, "Player Char")
        create_campaign(1)

        # Both connect
        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as dm_ws:
            with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as player_ws:
                # Consume connection notifications
                dm_ws.receive_json()  # user_connected for player

                # Player sends whispered roll
                player_ws.send_json(
                    {
                        "type": "dice_roll",
                        "data": {
                            "character_name": "Player Char",
                            "dice_type": 20,
                            "num_dice": 1,
                            "modifier": 0,
                            "whisper_to": "dm",
                        },
                    }
                )

                # DM should receive it (via send_to_user)
                dm_response = dm_ws.receive_json()
                assert dm_response["type"] == "dice_roll_result"
                assert dm_response["data"]["whisper_to"] == "dm"
                assert dm_response["data"]["character_name"] == "Player Char"

                # Player should also receive their own whispered roll
                player_response = player_ws.receive_json()
                assert player_response["type"] == "dice_roll_result"
                assert player_response["data"]["whisper_to"] == "dm"

    def test_whisper_to_specific_user(self):
        """Whisper to a specific user ID should only go to that user + sender."""
        dm_token = create_user("dm_w4", "dm_w4@test.com", is_dm=True)
        player_token = create_user("player_w4", "p_w4@test.com", is_dm=False)
        create_character(dm_token, "DM Char")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as dm_ws:
            with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as player_ws:
                # Consume connection notification
                dm_ws.receive_json()  # user_connected

                # DM whispers to player (user ID 2)
                dm_ws.send_json(
                    {
                        "type": "dice_roll",
                        "data": {
                            "character_name": "DM Char",
                            "dice_type": 20,
                            "num_dice": 1,
                            "modifier": 5,
                            "whisper_to": 2,
                        },
                    }
                )

                # Player should receive it
                player_response = player_ws.receive_json()
                assert player_response["type"] == "dice_roll_result"
                assert player_response["data"]["modifier"] == 5

                # DM should also receive their own whispered roll
                dm_response = dm_ws.receive_json()
                assert dm_response["type"] == "dice_roll_result"

    def test_whisper_roll_has_correct_total(self):
        """Whispered rolls should still compute total correctly."""
        dm_token = create_user("dm_w5", "dm_w5@test.com", is_dm=True)
        create_character(dm_token, "DM Char")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "DM Char",
                        "dice_type": 6,
                        "num_dice": 2,
                        "modifier": 3,
                        "whisper_to": "dm",
                    },
                }
            )
            response = ws.receive_json()
            data = response["data"]
            assert data["total"] == sum(data["rolls"]) + 3
            assert data["dice_type"] == 6
            assert data["num_dice"] == 2


class TestWhisperChatMessages:
    """Test whisper routing for chat messages."""

    def test_public_chat_broadcasts(self):
        """Chat without whisper broadcasts to all."""
        dm_token = create_user("dm_c1", "dm_c1@test.com", is_dm=True)
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "chat_message",
                    "data": {"message": "Hello everyone"},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "chat_message"
            assert response["data"]["message"] == "Hello everyone"
            assert response["data"]["whisper_to"] is None

    def test_whisper_chat_to_dm(self):
        """Whispered chat should include whisper_to field."""
        dm_token = create_user("dm_c2", "dm_c2@test.com", is_dm=True)
        player_token = create_user("player_c2", "p_c2@test.com", is_dm=False)
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as dm_ws:
            with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as player_ws:
                dm_ws.receive_json()  # user_connected

                # Player whispers to DM
                player_ws.send_json(
                    {
                        "type": "chat_message",
                        "data": {"message": "Secret message", "whisper_to": "dm"},
                    }
                )

                # DM gets it
                dm_response = dm_ws.receive_json()
                assert dm_response["type"] == "chat_message"
                assert dm_response["data"]["message"] == "Secret message"
                assert dm_response["data"]["whisper_to"] == "dm"

                # Player gets their copy
                player_response = player_ws.receive_json()
                assert player_response["type"] == "chat_message"
                assert player_response["data"]["whisper_to"] == "dm"

    def test_whisper_chat_to_specific_user(self):
        """Chat whispered to specific user goes only to that user + sender."""
        dm_token = create_user("dm_c3", "dm_c3@test.com", is_dm=True)
        player_token = create_user("player_c3", "p_c3@test.com", is_dm=False)
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as dm_ws:
            with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as player_ws:
                dm_ws.receive_json()  # user_connected

                # DM whispers to player (user ID 2)
                dm_ws.send_json(
                    {
                        "type": "chat_message",
                        "data": {"message": "Only you can see this", "whisper_to": 2},
                    }
                )

                # Player receives it
                player_response = player_ws.receive_json()
                assert player_response["data"]["message"] == "Only you can see this"

                # DM receives their copy
                dm_response = dm_ws.receive_json()
                assert dm_response["data"]["message"] == "Only you can see this"
