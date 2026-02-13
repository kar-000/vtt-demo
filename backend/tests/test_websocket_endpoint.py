"""Tests for WebSocket game endpoint in dice.py."""

import pytest
from app.core.database import Base, get_db
from app.main import app
from app.routes.dice import roll_dice
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
    """Helper to create a test user and return token."""
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


def create_campaign_and_char(dm_token, player_token=None):
    """Helper to create campaign and character, return campaign_id."""
    from app.models.campaign import Campaign

    db = TestingSessionLocal()
    campaign = Campaign(id=1, name="Test Campaign", dm_id=1, settings={})
    db.add(campaign)
    db.commit()
    db.close()

    # Create a character for combat tests
    client.post(
        "/api/v1/characters/",
        headers={"Authorization": f"Bearer {dm_token}"},
        json={
            "name": "Test Fighter",
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
            "speed": 30,
        },
    )
    return 1


class TestRollDice:
    """Test the roll_dice helper function."""

    def test_roll_single_d6(self):
        """Roll 1d6 returns a list with one result."""
        results = roll_dice(1, 6)
        assert len(results) == 1
        assert 1 <= results[0] <= 6

    def test_roll_multiple_dice(self):
        """Roll 3d8 returns 3 results in range."""
        results = roll_dice(3, 8)
        assert len(results) == 3
        for r in results:
            assert 1 <= r <= 8

    def test_roll_d20(self):
        """Roll 1d20 returns result 1-20."""
        results = roll_dice(1, 20)
        assert len(results) == 1
        assert 1 <= results[0] <= 20


class TestWebSocketAuth:
    """Test WebSocket authentication paths."""

    def test_invalid_token_closes_connection(self):
        """Invalid token should close the WebSocket."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws/game/1?token=invalidtoken") as ws:
                ws.receive_json()

    def test_missing_sub_in_token_closes(self):
        """Token without sub claim should close."""
        from app.core.config import settings
        from jose import jwt

        bad_token = jwt.encode({"no_sub": "here"}, settings.SECRET_KEY, algorithm="HS256")
        with pytest.raises(Exception):
            with client.websocket_connect(f"/api/v1/ws/game/1?token={bad_token}") as ws:
                ws.receive_json()

    def test_nonexistent_user_closes(self):
        """Token for nonexistent user should close."""
        from app.core.config import settings
        from jose import jwt

        token = jwt.encode({"sub": "99999"}, settings.SECRET_KEY, algorithm="HS256")
        with pytest.raises(Exception):
            with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
                ws.receive_json()


class TestDiceRollMessages:
    """Test dice roll WebSocket messages."""

    def test_dice_roll_valid(self):
        """Valid dice roll broadcasts result."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "dice_type": 20,
                        "num_dice": 1,
                        "modifier": 5,
                        "character_name": "Fighter",
                        "roll_type": "attack",
                        "label": "Longsword",
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "dice_roll_result"
            d = response["data"]
            assert d["dice_type"] == 20
            assert d["num_dice"] == 1
            assert d["modifier"] == 5
            assert len(d["rolls"]) == 1
            assert 1 <= d["rolls"][0] <= 20
            assert d["total"] == d["rolls"][0] + 5
            assert d["character_name"] == "Fighter"
            assert d["roll_type"] == "attack"
            assert d["label"] == "Longsword"

    def test_dice_roll_invalid_type(self):
        """Invalid dice type returns error."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json({"type": "dice_roll", "data": {"dice_type": 7, "num_dice": 1}})
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Invalid dice type" in response["message"]

    def test_dice_roll_defaults(self):
        """Dice roll with minimal data uses defaults."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json({"type": "dice_roll", "data": {"dice_type": 6}})
            response = ws.receive_json()
            assert response["type"] == "dice_roll_result"
            assert response["data"]["num_dice"] == 1
            assert response["data"]["modifier"] == 0


class TestChatMessages:
    """Test chat message handling."""

    def test_chat_message(self):
        """Chat message is broadcast."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "chat_message",
                    "data": {"message": "Hello adventurers!"},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "chat_message"
            assert response["data"]["message"] == "Hello adventurers!"
            assert response["data"]["username"] == "testdm"
            assert "timestamp" in response["data"]


class TestInitiativeActions:
    """Test initiative actions not covered by test_initiative.py."""

    def _start_combat(self, ws):
        """Helper to start combat and consume the response."""
        ws.send_json(
            {
                "type": "initiative_update",
                "data": {"action": "start_combat", "data": {}},
            }
        )
        return ws.receive_json()

    def _add_npc(self, ws, name="Goblin", initiative=10):
        """Helper to add an NPC."""
        ws.send_json(
            {
                "type": "initiative_update",
                "data": {
                    "action": "add_combatant",
                    "data": {
                        "name": name,
                        "initiative": initiative,
                        "speed": 30,
                        "max_hp": 7,
                        "armor_class": 15,
                        "attacks": [
                            {
                                "name": "Scimitar",
                                "attack_bonus": 4,
                                "damage_dice": "1d6+2",
                            }
                        ],
                        "dex_mod": 2,
                    },
                },
            }
        )
        return ws.receive_json()

    def test_roll_initiative_for_combatant(self):
        """Roll initiative for a specific combatant."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "roll_initiative",
                        "data": {"combatant_id": combatant_id},
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "initiative_state"
            # Should have an initiative value now
            combatants = response["data"]["combatants"]
            rolled = [c for c in combatants if c["id"] == combatant_id][0]
            assert rolled["initiative"] is not None
            assert "roll" in rolled

    def test_set_initiative_manually(self):
        """Manually set initiative value."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "set_initiative",
                        "data": {"combatant_id": combatant_id, "value": 18},
                    },
                }
            )
            response = ws.receive_json()
            combatants = response["data"]["combatants"]
            updated = [c for c in combatants if c["id"] == combatant_id][0]
            assert updated["initiative"] == 18

    def test_previous_turn(self):
        """Go back to previous turn."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            self._start_combat(ws)

            # Advance a turn first
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "next_turn", "data": {}},
                }
            )
            ws.receive_json()

            # Go back
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "previous_turn", "data": {}},
                }
            )
            response = ws.receive_json()
            assert response["data"]["current_turn_index"] == 0

    def test_previous_turn_wraps_to_previous_round(self):
        """Previous turn at index 0 wraps to last combatant."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            self._start_combat(ws)

            # Go back from index 0
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "previous_turn", "data": {}},
                }
            )
            response = ws.receive_json()
            # Should wrap to last combatant
            num_combatants = len(response["data"]["combatants"])
            assert response["data"]["current_turn_index"] == num_combatants - 1

    def test_use_action(self):
        """Mark action as used."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "use_action",
                        "data": {"combatant_id": combatant_id},
                    },
                }
            )
            response = ws.receive_json()
            c = [c for c in response["data"]["combatants"] if c["id"] == combatant_id][0]
            assert c["action_economy"]["action"] is False

    def test_use_bonus_action(self):
        """Mark bonus action as used."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "use_bonus_action",
                        "data": {"combatant_id": combatant_id},
                    },
                }
            )
            response = ws.receive_json()
            c = [c for c in response["data"]["combatants"] if c["id"] == combatant_id][0]
            assert c["action_economy"]["bonus_action"] is False

    def test_use_reaction(self):
        """Mark reaction as used."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "use_reaction",
                        "data": {"combatant_id": combatant_id},
                    },
                }
            )
            response = ws.receive_json()
            c = [c for c in response["data"]["combatants"] if c["id"] == combatant_id][0]
            assert c["action_economy"]["reaction"] is False

    def test_use_movement(self):
        """Deduct movement from combatant."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "use_movement",
                        "data": {"combatant_id": combatant_id, "amount": 15},
                    },
                }
            )
            response = ws.receive_json()
            c = [c for c in response["data"]["combatants"] if c["id"] == combatant_id][0]
            assert c["action_economy"]["movement"] == 15  # 30 - 15

    def test_reset_action_economy(self):
        """Reset action economy for combatant."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            state = self._start_combat(ws)
            combatant_id = state["data"]["combatants"][0]["id"]

            # Use action first
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "use_action",
                        "data": {"combatant_id": combatant_id},
                    },
                }
            )
            ws.receive_json()

            # Reset
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "reset_action_economy",
                        "data": {"combatant_id": combatant_id},
                    },
                }
            )
            response = ws.receive_json()
            c = [c for c in response["data"]["combatants"] if c["id"] == combatant_id][0]
            assert c["action_economy"]["action"] is True
            assert c["action_economy"]["bonus_action"] is True
            assert c["action_economy"]["reaction"] is True

    def test_update_npc_stats(self):
        """Update NPC HP and AC."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            self._start_combat(ws)
            npc_state = self._add_npc(ws)
            npc_id = [c for c in npc_state["data"]["combatants"] if c["type"] == "npc"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "update_npc",
                        "data": {
                            "combatant_id": npc_id,
                            "current_hp": 3,
                            "max_hp": 10,
                            "armor_class": 18,
                        },
                    },
                }
            )
            response = ws.receive_json()
            npc = [c for c in response["data"]["combatants"] if c["id"] == npc_id][0]
            assert npc["current_hp"] == 3
            assert npc["max_hp"] == 10
            assert npc["armor_class"] == 18

    def test_unknown_initiative_action(self):
        """Unknown initiative action returns error."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            self._start_combat(ws)

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "nonexistent_action", "data": {}},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Unknown initiative action" in response["message"]

    def test_initiative_without_campaign(self):
        """Initiative update on nonexistent campaign returns error."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)

        # Connect to a campaign that doesn't exist in DB
        with client.websocket_connect(f"/api/v1/ws/game/999?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "start_combat", "data": {}},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Campaign not found" in response["message"]

    def test_roll_all_initiative(self):
        """Roll all initiative covers the loop branch."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            self._start_combat(ws)

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "roll_all", "data": {}},
                }
            )
            response = ws.receive_json()
            # All combatants should have initiative now
            for c in response["data"]["combatants"]:
                assert c["initiative"] is not None


class TestMapUpdate:
    """Test map_update WebSocket message handling."""

    def test_dm_can_send_map_update(self):
        """DM can broadcast map updates."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "map_update",
                    "data": {
                        "action": "token_move",
                        "tokenId": "char-1",
                        "x": 5,
                        "y": 3,
                    },
                }
            )
            # DM sends but is excluded from broadcast, so no response expected
            # Send another message to verify connection is still active
            ws.send_json({"type": "dice_roll", "data": {"dice_type": 20, "num_dice": 1}})
            response = ws.receive_json()
            assert response["type"] == "dice_roll_result"

    def test_player_cannot_send_map_update(self):
        """Player gets error when trying to update map."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as ws:
            ws.send_json(
                {
                    "type": "map_update",
                    "data": {"action": "token_move", "tokenId": "char-1"},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Only the DM" in response["message"]


class TestUnknownMessage:
    """Test unknown message type handling."""

    def test_unknown_message_type(self):
        """Unknown message type returns error."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_and_char(dm_token)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json({"type": "totally_unknown", "data": {}})
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Unknown message type" in response["message"]
