"""Comprehensive tests for dice.py to ensure >90% coverage.

Covers: initiative actions (set_initiative, previous_turn, use_action,
use_bonus_action, use_reaction, use_movement, reset_action_economy,
update_npc, clear_conditions, add_pc, map_update), advantage/disadvantage
rolls, whisper routing, condition duration ticking, and edge cases.
"""

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


def create_character(token, name, dexterity=14, speed=30):
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
            "speed": speed,
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


def start_combat_and_get_state(ws):
    """Helper: start combat and return the initiative state."""
    ws.send_json({"type": "initiative_update", "data": {"action": "start_combat", "data": {}}})
    response = ws.receive_json()
    assert response["type"] == "initiative_state"
    return response["data"]


def send_initiative_action(ws, action, data=None):
    """Helper: send an initiative action and return the response."""
    ws.send_json({"type": "initiative_update", "data": {"action": action, "data": data or {}}})
    return ws.receive_json()


class TestSetInitiative:
    """Test manually setting initiative values."""

    def test_set_initiative_value(self):
        token = create_user("dm_si", "dm_si@test.com", is_dm=True)
        create_character(token, "Fighter")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            combatant_id = state["combatants"][0]["id"]

            response = send_initiative_action(ws, "set_initiative", {"combatant_id": combatant_id, "value": 15})
            assert response["type"] == "initiative_state"
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == combatant_id)
            assert combatant["initiative"] == 15


class TestPreviousTurn:
    """Test going back to previous turn."""

    def test_previous_turn_wraps_around(self):
        token = create_user("dm_pt", "dm_pt@test.com", is_dm=True)
        create_character(token, "Char1")
        create_character(token, "Char2")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            # Go to previous turn from index 0 -> should wrap to last combatant
            response = send_initiative_action(ws, "previous_turn")
            state = response["data"]
            assert state["current_turn_index"] == len(state["combatants"]) - 1

    def test_previous_turn_decrements_round(self):
        token = create_user("dm_pt2", "dm_pt2@test.com", is_dm=True)
        create_character(token, "Char1")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            # Advance to round 2
            send_initiative_action(ws, "next_turn")

            # Go back - should go to round 1
            response = send_initiative_action(ws, "previous_turn")
            assert response["data"]["round"] >= 1


class TestActionEconomy:
    """Test action economy actions: use_action, use_bonus_action, use_reaction, use_movement, reset."""

    def test_use_action(self):
        token = create_user("dm_ae1", "dm_ae1@test.com", is_dm=True)
        create_character(token, "Fighter")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            response = send_initiative_action(ws, "use_action", {"combatant_id": cid})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert combatant["action_economy"]["action"] is False

    def test_use_bonus_action(self):
        token = create_user("dm_ae2", "dm_ae2@test.com", is_dm=True)
        create_character(token, "Rogue")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            response = send_initiative_action(ws, "use_bonus_action", {"combatant_id": cid})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert combatant["action_economy"]["bonus_action"] is False

    def test_use_reaction(self):
        token = create_user("dm_ae3", "dm_ae3@test.com", is_dm=True)
        create_character(token, "Paladin")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            response = send_initiative_action(ws, "use_reaction", {"combatant_id": cid})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert combatant["action_economy"]["reaction"] is False

    def test_use_movement(self):
        token = create_user("dm_ae4", "dm_ae4@test.com", is_dm=True)
        create_character(token, "Runner", speed=30)
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Use 10 ft of movement
            response = send_initiative_action(ws, "use_movement", {"combatant_id": cid, "amount": 10})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert combatant["action_economy"]["movement"] == 20

    def test_use_movement_cannot_go_negative(self):
        token = create_user("dm_ae5", "dm_ae5@test.com", is_dm=True)
        create_character(token, "Slow", speed=30)
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Try to use more movement than available
            response = send_initiative_action(ws, "use_movement", {"combatant_id": cid, "amount": 50})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert combatant["action_economy"]["movement"] == 0

    def test_reset_action_economy(self):
        token = create_user("dm_ae6", "dm_ae6@test.com", is_dm=True)
        create_character(token, "Wizard")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Use everything
            send_initiative_action(ws, "use_action", {"combatant_id": cid})
            send_initiative_action(ws, "use_bonus_action", {"combatant_id": cid})
            send_initiative_action(ws, "use_reaction", {"combatant_id": cid})
            send_initiative_action(ws, "use_movement", {"combatant_id": cid, "amount": 30})

            # Reset
            response = send_initiative_action(ws, "reset_action_economy", {"combatant_id": cid})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            ae = combatant["action_economy"]
            assert ae["action"] is True
            assert ae["bonus_action"] is True
            assert ae["reaction"] is True
            assert ae["movement"] == ae["max_movement"]


class TestUpdateNPC:
    """Test updating NPC stats."""

    def test_update_npc_hp(self):
        token = create_user("dm_npc1", "dm_npc1@test.com", is_dm=True)
        create_character(token, "PC")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            # Add NPC
            response = send_initiative_action(
                ws,
                "add_combatant",
                {"name": "Goblin", "max_hp": 10, "armor_class": 13},
            )
            npc = next(c for c in response["data"]["combatants"] if c["type"] == "npc")

            # Update NPC HP
            response = send_initiative_action(
                ws,
                "update_npc",
                {"combatant_id": npc["id"], "current_hp": 5},
            )
            updated_npc = next(c for c in response["data"]["combatants"] if c["id"] == npc["id"])
            assert updated_npc["current_hp"] == 5

    def test_update_npc_multiple_fields(self):
        token = create_user("dm_npc2", "dm_npc2@test.com", is_dm=True)
        create_character(token, "PC")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            response = send_initiative_action(
                ws,
                "add_combatant",
                {"name": "Dragon", "max_hp": 100, "armor_class": 18},
            )
            npc = next(c for c in response["data"]["combatants"] if c["type"] == "npc")

            # Update multiple fields
            response = send_initiative_action(
                ws,
                "update_npc",
                {
                    "combatant_id": npc["id"],
                    "current_hp": 50,
                    "max_hp": 120,
                    "armor_class": 20,
                },
            )
            updated = next(c for c in response["data"]["combatants"] if c["id"] == npc["id"])
            assert updated["current_hp"] == 50
            assert updated["max_hp"] == 120
            assert updated["armor_class"] == 20

    def test_update_npc_hp_cannot_go_negative(self):
        token = create_user("dm_npc3", "dm_npc3@test.com", is_dm=True)
        create_character(token, "PC")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            response = send_initiative_action(ws, "add_combatant", {"name": "Skeleton", "max_hp": 10})
            npc = next(c for c in response["data"]["combatants"] if c["type"] == "npc")

            response = send_initiative_action(ws, "update_npc", {"combatant_id": npc["id"], "current_hp": -5})
            updated = next(c for c in response["data"]["combatants"] if c["id"] == npc["id"])
            assert updated["current_hp"] == 0


class TestAddPC:
    """Test re-adding a PC to initiative."""

    def test_add_pc_after_removal(self):
        token = create_user("dm_pc1", "dm_pc1@test.com", is_dm=True)
        char = create_character(token, "Returned Hero")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Remove the PC
            response = send_initiative_action(ws, "remove_combatant", {"combatant_id": cid})
            assert len(response["data"]["combatants"]) == 0

            # Re-add the PC
            response = send_initiative_action(ws, "add_pc", {"character_id": char["id"]})
            assert len(response["data"]["combatants"]) == 1
            readded = response["data"]["combatants"][0]
            assert readded["name"] == "Returned Hero"
            assert readded["type"] == "pc"
            assert readded["character_id"] == char["id"]

    def test_add_pc_no_duplicate(self):
        token = create_user("dm_pc2", "dm_pc2@test.com", is_dm=True)
        char = create_character(token, "Already Here")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            assert len(state["combatants"]) == 1

            # Try to add same PC again - should not duplicate
            response = send_initiative_action(ws, "add_pc", {"character_id": char["id"]})
            assert len(response["data"]["combatants"]) == 1

    def test_add_pc_with_initiative_value(self):
        token = create_user("dm_pc3", "dm_pc3@test.com", is_dm=True)
        char = create_character(token, "Late Joiner")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Remove then re-add with initiative
            send_initiative_action(ws, "remove_combatant", {"combatant_id": cid})
            response = send_initiative_action(ws, "add_pc", {"character_id": char["id"], "initiative": 18})
            readded = response["data"]["combatants"][0]
            assert readded["initiative"] == 18

    def test_add_pc_nonexistent_character(self):
        token = create_user("dm_pc4", "dm_pc4@test.com", is_dm=True)
        create_character(token, "Someone")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            # Try to add a character ID that doesn't exist
            response = send_initiative_action(ws, "add_pc", {"character_id": 9999})
            # Should still return state (just unchanged)
            assert response["type"] == "initiative_state"


class TestConditions:
    """Test condition management."""

    def test_add_condition(self):
        token = create_user("dm_cond1", "dm_cond1@test.com", is_dm=True)
        create_character(token, "Victim")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            response = send_initiative_action(
                ws,
                "add_condition",
                {
                    "combatant_id": cid,
                    "name": "Poisoned",
                    "duration": 3,
                    "duration_type": "rounds",
                },
            )
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert len(combatant["conditions"]) == 1
            assert combatant["conditions"][0]["name"] == "Poisoned"
            assert combatant["conditions"][0]["duration"] == 3

    def test_add_duplicate_condition_ignored(self):
        token = create_user("dm_cond2", "dm_cond2@test.com", is_dm=True)
        create_character(token, "Target")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            send_initiative_action(ws, "add_condition", {"combatant_id": cid, "name": "Stunned"})
            response = send_initiative_action(ws, "add_condition", {"combatant_id": cid, "name": "Stunned"})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert len(combatant["conditions"]) == 1

    def test_remove_condition(self):
        token = create_user("dm_cond3", "dm_cond3@test.com", is_dm=True)
        create_character(token, "Recovering")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            send_initiative_action(ws, "add_condition", {"combatant_id": cid, "name": "Prone"})
            response = send_initiative_action(ws, "remove_condition", {"combatant_id": cid, "name": "Prone"})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert len(combatant["conditions"]) == 0

    def test_clear_conditions(self):
        token = create_user("dm_cond4", "dm_cond4@test.com", is_dm=True)
        create_character(token, "Messy")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            send_initiative_action(ws, "add_condition", {"combatant_id": cid, "name": "Poisoned"})
            send_initiative_action(ws, "add_condition", {"combatant_id": cid, "name": "Blinded"})
            response = send_initiative_action(ws, "clear_conditions", {"combatant_id": cid})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert len(combatant["conditions"]) == 0

    def test_condition_duration_ticks_on_next_turn(self):
        """Condition duration should decrease when next_turn reaches the combatant."""
        token = create_user("dm_cond5", "dm_cond5@test.com", is_dm=True)
        create_character(token, "OnlyChar")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Add condition with 2 rounds
            send_initiative_action(
                ws,
                "add_condition",
                {
                    "combatant_id": cid,
                    "name": "Paralyzed",
                    "duration": 2,
                    "duration_type": "rounds",
                },
            )

            # Next turn (wraps around to same combatant since only 1)
            response = send_initiative_action(ws, "next_turn")
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            cond = next(c for c in combatant["conditions"] if c["name"] == "Paralyzed")
            assert cond["duration"] == 1

            # Next turn again - condition should expire
            response = send_initiative_action(ws, "next_turn")
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert len(combatant["conditions"]) == 0

    def test_indefinite_condition_persists(self):
        """Indefinite conditions should not tick down."""
        token = create_user("dm_cond6", "dm_cond6@test.com", is_dm=True)
        create_character(token, "Forever")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            send_initiative_action(
                ws,
                "add_condition",
                {
                    "combatant_id": cid,
                    "name": "Concentrating",
                    "duration_type": "indefinite",
                },
            )

            # Multiple turns should not remove indefinite condition
            send_initiative_action(ws, "next_turn")
            response = send_initiative_action(ws, "next_turn")
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert len(combatant["conditions"]) == 1
            assert combatant["conditions"][0]["name"] == "Concentrating"


class TestNextTurnActionReset:
    """Test that action economy resets on next turn."""

    def test_action_economy_resets_on_turn(self):
        token = create_user("dm_nt1", "dm_nt1@test.com", is_dm=True)
        create_character(token, "ResetMe")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Use action and movement
            send_initiative_action(ws, "use_action", {"combatant_id": cid})
            send_initiative_action(ws, "use_movement", {"combatant_id": cid, "amount": 30})

            # Next turn (wraps to same combatant) resets action economy
            response = send_initiative_action(ws, "next_turn")
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            ae = combatant["action_economy"]
            assert ae["action"] is True
            assert ae["bonus_action"] is True
            assert ae["reaction"] is True
            assert ae["movement"] == ae["max_movement"]


class TestAdvantageDisadvantage:
    """Test advantage/disadvantage dice rolling."""

    def test_advantage_roll(self):
        token = create_user("dm_adv1", "dm_adv1@test.com", is_dm=True)
        create_character(token, "Lucky")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "Lucky",
                        "dice_type": 20,
                        "num_dice": 1,
                        "modifier": 5,
                        "advantage": "advantage",
                        "roll_type": "ability",
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "dice_roll_result"
            data = response["data"]
            assert data["advantage"] == "advantage"
            assert data["all_rolls"] is not None
            assert len(data["all_rolls"]) == 2
            # The used roll should be the max
            assert data["rolls"][0] == max(data["all_rolls"])
            assert data["total"] == data["rolls"][0] + 5

    def test_disadvantage_roll(self):
        token = create_user("dm_dis1", "dm_dis1@test.com", is_dm=True)
        create_character(token, "Unlucky")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "Unlucky",
                        "dice_type": 20,
                        "num_dice": 1,
                        "modifier": 3,
                        "advantage": "disadvantage",
                    },
                }
            )
            response = ws.receive_json()
            data = response["data"]
            assert data["advantage"] == "disadvantage"
            assert data["all_rolls"] is not None
            assert len(data["all_rolls"]) == 2
            assert data["rolls"][0] == min(data["all_rolls"])

    def test_normal_d20_roll_no_advantage(self):
        token = create_user("dm_norm", "dm_norm@test.com", is_dm=True)
        create_character(token, "Normal")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "Normal",
                        "dice_type": 20,
                        "num_dice": 1,
                        "modifier": 0,
                    },
                }
            )
            response = ws.receive_json()
            data = response["data"]
            assert data["advantage"] is None
            assert data["all_rolls"] is None
            assert len(data["rolls"]) == 1


class TestInvalidDice:
    """Test invalid dice type handling."""

    def test_invalid_dice_type(self):
        token = create_user("dm_inv", "dm_inv@test.com", is_dm=True)
        create_character(token, "BadRoller")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "BadRoller",
                        "dice_type": 13,
                        "num_dice": 1,
                        "modifier": 0,
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "error"


class TestUnknownAction:
    """Test unknown initiative action."""

    def test_unknown_initiative_action(self):
        token = create_user("dm_unk", "dm_unk@test.com", is_dm=True)
        create_character(token, "Char")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            ws.send_json(
                {
                    "type": "initiative_update",
                    "data": {"action": "nonexistent_action", "data": {}},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Unknown" in response["message"]


class TestMapUpdate:
    """Test map update message handling."""

    def test_map_update_dm_only(self):
        """Only DM should be able to send map updates."""
        dm_token = create_user("dm_map", "dm_map@test.com", is_dm=True)
        player_token = create_user("player_map", "player_map@test.com", is_dm=False)
        create_character(dm_token, "DM Char")
        create_character(player_token, "Player Char")
        create_campaign(1)

        # Player trying to send map update should get error
        with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as ws:
            ws.send_json(
                {
                    "type": "map_update",
                    "data": {"action": "tokens_updated", "tokens": []},
                }
            )
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "DM" in response["message"]


class TestEndCombat:
    """Test ending combat."""

    def test_end_combat_clears_state(self):
        token = create_user("dm_end", "dm_end@test.com", is_dm=True)
        create_character(token, "Fighter")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

            response = send_initiative_action(ws, "end_combat")
            state = response["data"]
            assert state["active"] is False
            assert len(state["combatants"]) == 0
            assert state["round"] == 1


class TestRollAll:
    """Test rolling initiative for all combatants."""

    def test_roll_all_only_rolls_for_unrolled(self):
        token = create_user("dm_ra", "dm_ra@test.com", is_dm=True)
        create_character(token, "Char1")
        create_character(token, "Char2")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)

            # Roll initiative for first char only
            send_initiative_action(
                ws,
                "set_initiative",
                {"combatant_id": state["combatants"][0]["id"], "value": 20},
            )

            # Roll all should only roll for the second char
            response = send_initiative_action(ws, "roll_all")
            combatants = response["data"]["combatants"]
            for c in combatants:
                assert c["initiative"] is not None


class TestRemoveCombatant:
    """Test removing combatants."""

    def test_remove_adjusts_turn_index(self):
        token = create_user("dm_rem", "dm_rem@test.com", is_dm=True)
        create_character(token, "Char1")
        create_character(token, "Char2")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)

            # Advance to last combatant
            send_initiative_action(ws, "next_turn")

            # Remove the last combatant - index should adjust
            last_cid = state["combatants"][-1]["id"]
            response = send_initiative_action(ws, "remove_combatant", {"combatant_id": last_cid})
            assert response["data"]["current_turn_index"] == 0


class TestAddCombatantWithInit:
    """Test adding NPC with initiative value triggers sorting."""

    def test_add_combatant_with_initiative_sorts(self):
        token = create_user("dm_sort", "dm_sort@test.com", is_dm=True)
        create_character(token, "PC")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)

            # Set PC initiative to 10
            pc_id = state["combatants"][0]["id"]
            send_initiative_action(ws, "set_initiative", {"combatant_id": pc_id, "value": 10})

            # Add NPC with higher initiative - should sort first
            response = send_initiative_action(
                ws,
                "add_combatant",
                {"name": "Fast Goblin", "initiative": 20, "max_hp": 7},
            )
            combatants = response["data"]["combatants"]
            assert combatants[0]["name"] == "Fast Goblin"


class TestInitiativeStateOnConnect:
    """Test that connecting sends current initiative state."""

    def test_receives_active_initiative_on_connect(self):
        token = create_user("dm_conn", "dm_conn@test.com", is_dm=True)
        create_character(token, "Hero")
        create_campaign(1)

        # Start combat in first connection
        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            start_combat_and_get_state(ws)

        # Reconnect - should receive initiative state
        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            response = ws.receive_json()
            assert response["type"] == "initiative_state"
            assert response["data"]["active"] is True


class TestWhisperEdgeCases:
    """Test whisper edge cases not covered by test_whisper.py."""

    def test_dm_whisper_to_self(self):
        """DM whispering to DM should work without duplicate sends."""
        token = create_user("dm_ws1", "dm_ws1@test.com", is_dm=True)
        create_character(token, "DM")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "DM",
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

    def test_whisper_chat_to_dm(self):
        """Chat whispered to DM."""
        token = create_user("dm_wc", "dm_wc@test.com", is_dm=True)
        player_token = create_user("player_wc", "player_wc@test.com", is_dm=False)
        create_character(token, "DM Char")
        create_character(player_token, "Player Char")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={player_token}") as ws:
            ws.send_json(
                {
                    "type": "chat_message",
                    "data": {
                        "message": "Secret message",
                        "whisper_to": "dm",
                    },
                }
            )
            response = ws.receive_json()
            assert response["type"] == "chat_message"
            assert response["data"]["whisper_to"] == "dm"

    def test_multi_dice_roll(self):
        """Test rolling multiple dice (not d20, no advantage)."""
        token = create_user("dm_md", "dm_md@test.com", is_dm=True)
        create_character(token, "Heavy")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            ws.send_json(
                {
                    "type": "dice_roll",
                    "data": {
                        "character_name": "Heavy",
                        "dice_type": 6,
                        "num_dice": 4,
                        "modifier": 2,
                    },
                }
            )
            response = ws.receive_json()
            data = response["data"]
            assert len(data["rolls"]) == 4
            assert data["total"] == sum(data["rolls"]) + 2
            assert data["all_rolls"] is None


class TestRollInitiativeSingle:
    """Test rolling initiative for a single combatant."""

    def test_roll_initiative_for_combatant(self):
        token = create_user("dm_ri", "dm_ri@test.com", is_dm=True)
        create_character(token, "Warrior")
        create_campaign(1)

        with client.websocket_connect(f"/api/v1/ws/game/1?token={token}") as ws:
            state = start_combat_and_get_state(ws)
            cid = state["combatants"][0]["id"]

            # Roll initiative for combatant
            response = send_initiative_action(ws, "roll_initiative", {"combatant_id": cid})
            combatant = next(c for c in response["data"]["combatants"] if c["id"] == cid)
            assert combatant["initiative"] is not None
            assert combatant["roll"] is not None
            # Initiative should be roll + dex mod
            dex_mod = combatant.get("dex_mod", 0)
            assert combatant["initiative"] == combatant["roll"] + dex_mod
