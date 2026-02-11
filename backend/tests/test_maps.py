"""Tests for battle map endpoints."""

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


def create_user(username: str, email: str, is_dm: bool = False) -> str:
    """Create a user and return their token."""
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


def create_campaign(token: str, name: str = "Test Campaign") -> int:
    """Create a campaign and return its ID."""
    from app.core.security import decode_access_token
    from app.models.campaign import Campaign

    db = TestingSessionLocal()
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))

        campaign = Campaign(
            name=name,
            dm_id=user_id,
            description="Test campaign",
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign.id
    finally:
        db.close()


class TestMapsCRUD:
    """Tests for basic map CRUD operations."""

    def test_create_map(self):
        """DM can create a new map."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Dungeon Level 1",
                "description": "First level of the dungeon",
                "grid_width": 30,
                "grid_height": 20,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dungeon Level 1"
        assert data["description"] == "First level of the dungeon"
        assert data["grid_width"] == 30
        assert data["grid_height"] == 20
        assert data["is_active"] is False
        assert data["tokens"] == []

    def test_player_cannot_create_map(self):
        """Players cannot create maps."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {player_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Player Map",
            },
        )

        assert response.status_code == 403
        assert "Only the DM" in response.json()["detail"]

    def test_create_map_invalid_campaign(self):
        """Cannot create map for non-existent campaign."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": 99999,
                "name": "Invalid Map",
            },
        )

        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]

    def test_get_map(self):
        """Can retrieve a specific map."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Test Map",
            },
        )
        map_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Map"

    def test_get_nonexistent_map(self):
        """Getting a non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.get(
            "/api/v1/maps/99999",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 404
        assert "Map not found" in response.json()["detail"]

    def test_list_campaign_maps(self):
        """Can list all maps in a campaign."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        # Create multiple maps
        for i in range(3):
            client.post(
                "/api/v1/maps/",
                headers={"Authorization": f"Bearer {dm_token}"},
                json={
                    "campaign_id": campaign_id,
                    "name": f"Map {i}",
                },
            )

        response = client.get(
            f"/api/v1/maps/campaign/{campaign_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        maps = response.json()
        assert len(maps) == 3

    def test_list_maps_invalid_campaign(self):
        """Listing maps for non-existent campaign returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.get(
            "/api/v1/maps/campaign/99999",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]

    def test_update_map(self):
        """DM can update a map."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Original Name",
            },
        )
        map_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "name": "Updated Name",
                "description": "New description",
            },
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["description"] == "New description"

    def test_player_cannot_update_map(self):
        """Players cannot update maps."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Test Map",
            },
        )
        map_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {player_token}"},
            json={"name": "Hacked Name"},
        )

        assert response.status_code == 403
        assert "Only the DM" in response.json()["detail"]

    def test_update_nonexistent_map(self):
        """Updating non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.put(
            "/api/v1/maps/99999",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"name": "New Name"},
        )

        assert response.status_code == 404
        assert "Map not found" in response.json()["detail"]

    def test_delete_map(self):
        """DM can delete a map."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Map to Delete",
            },
        )
        map_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )
        assert get_response.status_code == 404

    def test_player_cannot_delete_map(self):
        """Players cannot delete maps."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Test Map",
            },
        )
        map_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert response.status_code == 403
        assert "Only the DM" in response.json()["detail"]

    def test_delete_nonexistent_map(self):
        """Deleting non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.delete(
            "/api/v1/maps/99999",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 404
        assert "Map not found" in response.json()["detail"]


class TestMapActivation:
    """Tests for map activation."""

    def test_activate_map(self):
        """DM can activate a map."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Test Map",
            },
        )
        map_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/maps/{map_id}/activate",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_activate_map_deactivates_others(self):
        """Activating a map deactivates other maps in the campaign."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        # Create and activate first map
        map1_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Map 1"},
        )
        map1_id = map1_response.json()["id"]

        client.post(
            f"/api/v1/maps/{map1_id}/activate",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        # Create and activate second map
        map2_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Map 2"},
        )
        map2_id = map2_response.json()["id"]

        client.post(
            f"/api/v1/maps/{map2_id}/activate",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        # Check that map 1 is now deactivated
        map1_check = client.get(
            f"/api/v1/maps/{map1_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )
        assert map1_check.json()["is_active"] is False

        # Check that map 2 is active
        map2_check = client.get(
            f"/api/v1/maps/{map2_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )
        assert map2_check.json()["is_active"] is True

    def test_player_cannot_activate_map(self):
        """Players cannot activate maps."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/maps/{map_id}/activate",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert response.status_code == 403

    def test_activate_nonexistent_map(self):
        """Activating non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.post(
            "/api/v1/maps/99999/activate",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 404

    def test_get_active_map(self):
        """Can get the currently active map for a campaign."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Active Map"},
        )
        map_id = create_response.json()["id"]

        client.post(
            f"/api/v1/maps/{map_id}/activate",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        response = client.get(
            f"/api/v1/maps/campaign/{campaign_id}/active",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Active Map"
        assert response.json()["is_active"] is True

    def test_get_active_map_none_active(self):
        """Getting active map when none is active returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        # Create but don't activate
        client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Inactive Map"},
        )

        response = client.get(
            f"/api/v1/maps/campaign/{campaign_id}/active",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 404
        assert "No active map" in response.json()["detail"]

    def test_get_active_map_invalid_campaign(self):
        """Getting active map for invalid campaign returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.get(
            "/api/v1/maps/campaign/99999/active",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 404
        assert "Campaign not found" in response.json()["detail"]


class TestTokenOperations:
    """Tests for token management on maps."""

    def test_update_tokens(self):
        """DM can update all tokens on a map."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        tokens = [
            {"id": "token-1", "name": "Goblin 1", "x": 5, "y": 5, "size": 1, "color": "#ff0000"},
            {"id": "token-2", "name": "Goblin 2", "x": 6, "y": 5, "size": 1, "color": "#ff0000"},
        ]

        response = client.patch(
            f"/api/v1/maps/{map_id}/tokens",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"tokens": tokens},
        )

        assert response.status_code == 200
        assert len(response.json()["tokens"]) == 2
        assert response.json()["tokens"][0]["name"] == "Goblin 1"

    def test_player_cannot_update_tokens(self):
        """Players cannot update tokens."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/maps/{map_id}/tokens",
            headers={"Authorization": f"Bearer {player_token}"},
            json={"tokens": []},
        )

        assert response.status_code == 403

    def test_update_tokens_nonexistent_map(self):
        """Updating tokens on non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.patch(
            "/api/v1/maps/99999/tokens",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"tokens": []},
        )

        assert response.status_code == 404

    def test_move_token(self):
        """DM can move a single token."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        # Add a token
        client.patch(
            f"/api/v1/maps/{map_id}/tokens",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"tokens": [{"id": "token-1", "name": "Goblin", "x": 0, "y": 0, "size": 1, "color": "#ff0000"}]},
        )

        # Move the token
        response = client.patch(
            f"/api/v1/maps/{map_id}/token/move",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"token_id": "token-1", "x": 10, "y": 15},
        )

        assert response.status_code == 200
        token = response.json()["tokens"][0]
        assert token["x"] == 10
        assert token["y"] == 15

    def test_player_cannot_move_token(self):
        """Players cannot move tokens (for now)."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        # Add a token as DM
        client.patch(
            f"/api/v1/maps/{map_id}/tokens",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"tokens": [{"id": "token-1", "name": "Goblin", "x": 0, "y": 0, "size": 1, "color": "#ff0000"}]},
        )

        # Player tries to move
        response = client.patch(
            f"/api/v1/maps/{map_id}/token/move",
            headers={"Authorization": f"Bearer {player_token}"},
            json={"token_id": "token-1", "x": 10, "y": 10},
        )

        assert response.status_code == 403

    def test_move_nonexistent_token(self):
        """Moving a non-existent token returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/maps/{map_id}/token/move",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"token_id": "nonexistent", "x": 10, "y": 10},
        )

        assert response.status_code == 404
        assert "Token not found" in response.json()["detail"]

    def test_move_token_nonexistent_map(self):
        """Moving token on non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.patch(
            "/api/v1/maps/99999/token/move",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"token_id": "token-1", "x": 10, "y": 10},
        )

        assert response.status_code == 404


class TestFogOfWar:
    """Tests for fog of war operations."""

    def test_set_revealed_cells(self):
        """DM can set revealed cells."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map", "fog_enabled": True},
        )
        map_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}],
                "action": "set",
            },
        )

        assert response.status_code == 200
        assert len(response.json()["revealed_cells"]) == 3

    def test_add_revealed_cells(self):
        """DM can add to revealed cells."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map", "fog_enabled": True},
        )
        map_id = create_response.json()["id"]

        # Set initial cells
        client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}],
                "action": "set",
            },
        )

        # Add more cells
        response = client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 1, "y": 0}, {"x": 2, "y": 0}],
                "action": "add",
            },
        )

        assert response.status_code == 200
        assert len(response.json()["revealed_cells"]) == 3

    def test_add_revealed_cells_no_duplicates(self):
        """Adding duplicate cells doesn't create duplicates."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map", "fog_enabled": True},
        )
        map_id = create_response.json()["id"]

        # Set initial cell
        client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}],
                "action": "set",
            },
        )

        # Try to add duplicate
        response = client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}, {"x": 1, "y": 0}],
                "action": "add",
            },
        )

        assert response.status_code == 200
        assert len(response.json()["revealed_cells"]) == 2

    def test_remove_revealed_cells(self):
        """DM can remove revealed cells."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map", "fog_enabled": True},
        )
        map_id = create_response.json()["id"]

        # Set initial cells
        client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}],
                "action": "set",
            },
        )

        # Remove some cells
        response = client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 1, "y": 0}],
                "action": "remove",
            },
        )

        assert response.status_code == 200
        assert len(response.json()["revealed_cells"]) == 2

    def test_player_cannot_update_fog(self):
        """Players cannot update fog of war."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)
        player_token = create_user("player1", "player1@example.com")

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map", "fog_enabled": True},
        )
        map_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/maps/{map_id}/fog",
            headers={"Authorization": f"Bearer {player_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}],
                "action": "set",
            },
        )

        assert response.status_code == 403

    def test_fog_update_nonexistent_map(self):
        """Updating fog on non-existent map returns 404."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)

        response = client.patch(
            "/api/v1/maps/99999/fog",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "revealed_cells": [{"x": 0, "y": 0}],
                "action": "set",
            },
        )

        assert response.status_code == 404


class TestMapWithImageData:
    """Tests for maps with image data."""

    def test_create_map_with_image(self):
        """Can create a map with base64 image data."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        # Small valid base64 image (1x1 pixel transparent PNG)
        image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Map with Image",
                "image_data": image_data,
            },
        )

        assert response.status_code == 201
        assert response.json()["image_data"] == image_data

    def test_update_map_image(self):
        """Can update a map's image."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        response = client.put(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"image_data": image_data},
        )

        assert response.status_code == 200
        assert response.json()["image_data"] == image_data

    def test_list_maps_excludes_image_data(self):
        """Listing maps doesn't include image data (for performance)."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Map with Image",
                "image_data": image_data,
            },
        )

        response = client.get(
            f"/api/v1/maps/campaign/{campaign_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        maps = response.json()
        assert len(maps) == 1
        # MapListResponse doesn't include image_data
        assert "image_data" not in maps[0]


class TestMapGridConfiguration:
    """Tests for grid configuration."""

    def test_create_map_with_custom_grid(self):
        """Can create a map with custom grid settings."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "campaign_id": campaign_id,
                "name": "Custom Grid Map",
                "grid_size": 50,
                "grid_width": 40,
                "grid_height": 30,
                "show_grid": False,
                "grid_color": "rgba(0, 0, 0, 0.5)",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["grid_size"] == 50
        assert data["grid_width"] == 40
        assert data["grid_height"] == 30
        assert data["show_grid"] is False
        assert data["grid_color"] == "rgba(0, 0, 0, 0.5)"

    def test_update_grid_settings(self):
        """Can update grid settings."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={
                "grid_size": 60,
                "show_grid": False,
            },
        )

        assert response.status_code == 200
        assert response.json()["grid_size"] == 60
        assert response.json()["show_grid"] is False


class TestMapActivationViaUpdate:
    """Tests for activating maps via update endpoint."""

    def test_activate_via_update(self):
        """Can activate a map via the update endpoint."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        create_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Test Map"},
        )
        map_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/maps/{map_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"is_active": True},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_activate_via_update_deactivates_others(self):
        """Activating via update deactivates other maps."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        # Create and activate first map
        map1_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Map 1"},
        )
        map1_id = map1_response.json()["id"]

        client.put(
            f"/api/v1/maps/{map1_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"is_active": True},
        )

        # Create and activate second map via update
        map2_response = client.post(
            "/api/v1/maps/",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"campaign_id": campaign_id, "name": "Map 2"},
        )
        map2_id = map2_response.json()["id"]

        client.put(
            f"/api/v1/maps/{map2_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
            json={"is_active": True},
        )

        # Verify map 1 is deactivated
        map1_check = client.get(
            f"/api/v1/maps/{map1_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )
        assert map1_check.json()["is_active"] is False
