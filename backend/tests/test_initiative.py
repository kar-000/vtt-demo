"""Tests for initiative tracker functionality."""

import pytest
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create test database (uses same as other tests for consistency)
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
    """Helper to create a test user."""
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


def create_character(token, name, dexterity=14):
    """Helper to create a test character."""
    response = client.post(
        "/api/v1/characters/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "race": "Human",
            "character_class": "Fighter",
            "level": 5,
            "strength": 16,
            "dexterity": dexterity,
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
    return response.json()


def create_campaign(db, dm_id):
    """Helper to create a campaign directly in DB."""
    from app.models.campaign import Campaign

    campaign = Campaign(
        id=1,
        name="Test Campaign",
        dm_id=dm_id,
        maps=[],
        settings={},
    )
    db.add(campaign)
    db.commit()
    return campaign


class TestInitiativeMultipleUsers:
    """Test that initiative includes characters from all users."""

    def test_start_combat_includes_all_characters(self):
        """Starting combat should include characters from ALL users, not just the DM."""
        # Create DM user
        dm_token = create_user("dm_user1", "dm1@test.com", is_dm=True)
        dm_char = create_character(dm_token, "DM Character", dexterity=14)

        # Create player user
        player_token = create_user("player_user1", "player1@test.com", is_dm=False)
        player_char = create_character(player_token, "Player Character", dexterity=16)

        # Create campaign
        db = TestingSessionLocal()
        create_campaign(db, 1)  # DM user ID is 1
        db.close()

        # Connect as DM and start combat via WebSocket
        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            # Start combat
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "start_combat",
                        "data": {"character_ids": [dm_char["id"]]},  # Only DM's char ID passed
                    },
                }
            )

            # Receive initiative state
            response = ws.receive_json()
            assert response["type"] == "initiative_state"

            initiative = response["data"]
            assert initiative["active"] is True
            assert len(initiative["combatants"]) == 2  # Both characters included

            # Verify both characters are present
            names = [c["name"] for c in initiative["combatants"]]
            assert "DM Character" in names
            assert "Player Character" in names

    def test_start_combat_with_multiple_player_characters(self):
        """Start combat with characters from 3 different players."""
        # Create users
        dm_token = create_user("dm2", "dm2@test.com", is_dm=True)
        player1_token = create_user("player2a", "p2a@test.com")
        player2_token = create_user("player2b", "p2b@test.com")

        # Create characters
        dm_char = create_character(dm_token, "Dungeon Master NPC")
        p1_char = create_character(player1_token, "Aragorn")
        p2_char = create_character(player2_token, "Legolas")

        # Create campaign
        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        # Start combat
        with client.websocket_connect(f"/api/v1/ws/game/1?token={dm_token}") as ws:
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "start_combat", "data": {}},
                }
            )

            response = ws.receive_json()
            initiative = response["data"]

            assert len(initiative["combatants"]) == 3
            names = [c["name"] for c in initiative["combatants"]]
            assert "Dungeon Master NPC" in names
            assert "Aragorn" in names
            assert "Legolas" in names


class TestInitiativePersistence:
    """Test that initiative values persist correctly."""

    def test_initiative_persists_after_next_turn(self):
        """Initiative values should NOT be wiped when advancing turns."""
        # Setup
        token = create_user("testuser", "test@test.com", is_dm=True)
        char1 = create_character(token, "Fighter", dexterity=14)
        char2 = create_character(token, "Rogue", dexterity=18)

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            # Start combat
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "start_combat", "data": {}},
                }
            )
            ws.receive_json()  # Consume start response

            # Roll all initiative
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "roll_all", "data": {}},
                }
            )
            roll_response = ws.receive_json()
            combatants_after_roll = roll_response["data"]["combatants"]

            # Store initiative values
            init_values_before = {c["id"]: c["initiative"] for c in combatants_after_roll}
            assert all(v is not None for v in init_values_before.values())

            # Advance turn
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "next_turn", "data": {}},
                }
            )
            next_response = ws.receive_json()
            combatants_after_next = next_response["data"]["combatants"]

            # Verify initiative values are preserved
            init_values_after = {c["id"]: c["initiative"] for c in combatants_after_next}
            assert init_values_before == init_values_after

    def test_initiative_persists_through_multiple_turns(self):
        """Initiative values persist through a full round of turns."""
        token = create_user("testuser", "test@test.com", is_dm=True)
        create_character(token, "Char1")
        create_character(token, "Char2")
        create_character(token, "Char3")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            # Start and roll
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            ws.receive_json()

            ws.send_json({"type": "initiative_update", "data": {"action": "roll_all", "data": {}}})
            response = ws.receive_json()
            original_values = {c["id"]: c["initiative"] for c in response["data"]["combatants"]}

            # Advance through full round (3 turns) plus one more
            for i in range(4):
                ws.send_json({"type": "initiative_update", "data": {"action": "next_turn", "data": {}}})
                response = ws.receive_json()

            # Check values after full round
            final_values = {c["id"]: c["initiative"] for c in response["data"]["combatants"]}
            assert original_values == final_values
            assert response["data"]["round"] == 2  # Should be on round 2

    def test_initiative_persists_after_reconnect(self):
        """Initiative state should be restored when reconnecting."""
        token = create_user("testuser", "test@test.com", is_dm=True)
        create_character(token, "TestChar")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        # First connection: start combat and roll
        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            ws.receive_json()

            ws.send_json({"type": "initiative_update", "data": {"action": "roll_all", "data": {}}})
            response = ws.receive_json()
            original_initiative = response["data"]["combatants"][0]["initiative"]

        # Second connection: check state is preserved
        # Note: The current implementation doesn't send initial state on connect,
        # but we can verify by advancing turn (which reads from DB)
        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "next_turn", "data": {}}})
            response = ws.receive_json()

            # State should be preserved from database
            assert response["data"]["active"] is True
            assert response["data"]["combatants"][0]["initiative"] == original_initiative


class TestInitiativeActions:
    """Test individual initiative actions."""

    def test_add_npc_with_initiative(self):
        """Adding NPC with set initiative value."""
        token = create_user("dm_npc", "dm_npc@test.com", is_dm=True)
        create_character(token, "PC")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            # Start combat
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            ws.receive_json()

            # Add NPC with initiative 15
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "add_combatant", "data": {"name": "Goblin", "initiative": 15}},
                }
            )
            response = ws.receive_json()

            combatants = response["data"]["combatants"]
            goblin = next(c for c in combatants if c["name"] == "Goblin")
            assert goblin["initiative"] == 15
            assert goblin["type"] == "npc"

    def test_remove_combatant(self):
        """Removing a combatant from initiative."""
        token = create_user("dm_remove", "dm_remove@test.com", is_dm=True)
        char = create_character(token, "TestChar")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            response = ws.receive_json()

            combatant_id = response["data"]["combatants"][0]["id"]

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "remove_combatant", "data": {"combatant_id": combatant_id}},
                }
            )
            response = ws.receive_json()

            assert len(response["data"]["combatants"]) == 0

    def test_end_combat_clears_state(self):
        """Ending combat clears all initiative state."""
        token = create_user("dm_end", "dm_end@test.com", is_dm=True)
        create_character(token, "TestChar")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            ws.receive_json()

            ws.send_json({"type": "initiative_update", "data": {"action": "end_combat", "data": {}}})
            response = ws.receive_json()

            assert response["data"]["active"] is False
            assert response["data"]["combatants"] == []
            assert response["data"]["round"] == 1

    def test_round_increments_on_full_cycle(self):
        """Round counter increments when cycling back to first combatant."""
        token = create_user("dm_round", "dm_round@test.com", is_dm=True)
        create_character(token, "Char1")
        create_character(token, "Char2")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            ws.receive_json()

            ws.send_json({"type": "initiative_update", "data": {"action": "roll_all", "data": {}}})
            ws.receive_json()

            # First turn advance
            ws.send_json({"type": "initiative_update", "data": {"action": "next_turn", "data": {}}})
            response = ws.receive_json()
            assert response["data"]["round"] == 1
            assert response["data"]["current_turn_index"] == 1

            # Second turn advance - should wrap and increment round
            ws.send_json({"type": "initiative_update", "data": {"action": "next_turn", "data": {}}})
            response = ws.receive_json()
            assert response["data"]["round"] == 2
            assert response["data"]["current_turn_index"] == 0


class TestConditions:
    """Test condition add/remove on combatants."""

    def test_add_condition_to_combatant(self):
        """Adding a condition should persist in the initiative state."""
        token = create_user("dm_cond", "dm_cond@test.com", is_dm=True)
        create_character(token, "Fighter")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            # Start combat
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            response = ws.receive_json()
            combatant_id = response["data"]["combatants"][0]["id"]

            # Add condition
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "add_condition",
                        "data": {
                            "combatant_id": combatant_id,
                            "name": "Prone",
                            "duration_type": "indefinite",
                        },
                    },
                }
            )
            response = ws.receive_json()

            # Verify condition is present
            combatant = response["data"]["combatants"][0]
            assert "conditions" in combatant
            assert len(combatant["conditions"]) == 1
            assert combatant["conditions"][0]["name"] == "Prone"

    def test_condition_persists_after_next_turn(self):
        """Indefinite conditions should survive turn changes."""
        token = create_user("dm_cond2", "dm_cond2@test.com", is_dm=True)
        create_character(token, "Fighter")
        create_character(token, "Rogue")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            response = ws.receive_json()
            combatant_id = response["data"]["combatants"][0]["id"]

            # Add indefinite condition
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {
                        "action": "add_condition",
                        "data": {
                            "combatant_id": combatant_id,
                            "name": "Blinded",
                            "duration_type": "indefinite",
                        },
                    },
                }
            )
            ws.receive_json()

            # Advance turn
            ws.send_json({"type": "initiative_update", "data": {"action": "next_turn", "data": {}}})
            response = ws.receive_json()

            # Condition should still be on the combatant
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == combatant_id)
            assert len(combatant["conditions"]) == 1
            assert combatant["conditions"][0]["name"] == "Blinded"

    def test_remove_condition(self):
        """Removing a condition should work."""
        token = create_user("dm_cond3", "dm_cond3@test.com", is_dm=True)
        create_character(token, "Fighter")

        db = TestingSessionLocal()
        create_campaign(db, 1)
        db.close()

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
            response = ws.receive_json()
            combatant_id = response["data"]["combatants"][0]["id"]

            # Add then remove condition
            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "add_condition", "data": {"combatant_id": combatant_id, "name": "Stunned"}},
                }
            )
            ws.receive_json()

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "remove_condition", "data": {"combatant_id": combatant_id, "name": "Stunned"}},
                }
            )
            response = ws.receive_json()

            combatant = response["data"]["combatants"][0]
            assert len(combatant.get("conditions", [])) == 0
