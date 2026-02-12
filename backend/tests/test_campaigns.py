"""Tests for campaign endpoints."""

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


def create_campaign_db(token: str, name: str = "Test Campaign") -> dict:
    """Create a campaign via API and return the response data."""
    response = client.post(
        "/api/v1/campaigns/",
        json={"name": name, "description": "A test campaign"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()


def create_character(token: str, name: str = "Test Character") -> dict:
    """Create a character via API and return the response data."""
    response = client.post(
        "/api/v1/characters/",
        json={
            "name": name,
            "race": "Human",
            "character_class": "Fighter",
            "level": 1,
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
            "max_hp": 12,
            "current_hp": 12,
            "armor_class": 16,
            "speed": 30,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()


class TestCampaignCreate:
    """Tests for creating campaigns."""

    def test_create_campaign_as_dm(self):
        """DM can create a campaign."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "New Campaign", "description": "An epic adventure"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Campaign"
        assert data["description"] == "An epic adventure"

    def test_create_campaign_without_description(self):
        """DM can create a campaign without description."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "Minimal Campaign"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Campaign"
        assert data["description"] is None

    def test_create_campaign_as_player_fails(self):
        """Players cannot create campaigns."""
        token = create_user("testplayer", "player@test.com", is_dm=False)
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "Player Campaign"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "Only DMs can create campaigns" in response.json()["detail"]

    def test_create_campaign_unauthenticated_fails(self):
        """Unauthenticated users cannot create campaigns."""
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "Unauthorized Campaign"},
        )
        assert response.status_code == 401


class TestCampaignList:
    """Tests for listing campaigns."""

    def test_dm_sees_all_campaigns(self):
        """DM can see all campaigns."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        create_campaign_db(token, "Campaign 1")
        create_campaign_db(token, "Campaign 2")

        response = client.get(
            "/api/v1/campaigns/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_player_sees_own_campaigns(self):
        """Player only sees campaigns they're in."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token, "Test Campaign")
        char = create_character(player_token)

        # Join character to campaign
        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/join/{char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200

        # Player should see the campaign
        response = client.get(
            "/api/v1/campaigns/",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Campaign"

    def test_player_without_campaign_sees_empty(self):
        """Player without campaign sees empty list."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)
        create_campaign_db(dm_token)

        response = client.get(
            "/api/v1/campaigns/",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestCampaignGet:
    """Tests for getting a specific campaign."""

    def test_dm_can_get_campaign(self):
        """DM can get any campaign."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        campaign = create_campaign_db(token)

        response = client.get(
            f"/api/v1/campaigns/{campaign['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Campaign"

    def test_player_in_campaign_can_get(self):
        """Player with character in campaign can get it."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)
        char = create_character(player_token)

        # Join campaign
        client.post(
            f"/api/v1/campaigns/{campaign['id']}/join/{char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        response = client.get(
            f"/api/v1/campaigns/{campaign['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200

    def test_player_not_in_campaign_denied(self):
        """Player without character in campaign is denied."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)

        response = client.get(
            f"/api/v1/campaigns/{campaign['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 403

    def test_nonexistent_campaign_404(self):
        """Nonexistent campaign returns 404."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        response = client.get(
            "/api/v1/campaigns/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestCampaignUpdate:
    """Tests for updating campaigns."""

    def test_dm_can_update_own_campaign(self):
        """DM can update their own campaign."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        campaign = create_campaign_db(token)

        response = client.put(
            f"/api/v1/campaigns/{campaign['id']}",
            json={
                "name": "Updated Campaign",
                "description": "New description",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign"
        assert data["description"] == "New description"

    def test_other_dm_cannot_update(self):
        """Another DM cannot update the campaign."""
        dm1_token = create_user("testdm1", "dm1@test.com", is_dm=True)
        dm2_token = create_user("testdm2", "dm2@test.com", is_dm=True)

        campaign = create_campaign_db(dm1_token)

        response = client.put(
            f"/api/v1/campaigns/{campaign['id']}",
            json={"name": "Hijacked"},
            headers={"Authorization": f"Bearer {dm2_token}"},
        )
        assert response.status_code == 403


class TestCampaignDelete:
    """Tests for deleting campaigns."""

    def test_dm_can_delete_own_campaign(self):
        """DM can delete their own campaign."""
        token = create_user("testdm", "dm@test.com", is_dm=True)
        campaign = create_campaign_db(token)

        response = client.delete(
            f"/api/v1/campaigns/{campaign['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(
            f"/api/v1/campaigns/{campaign['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_player_cannot_delete_campaign(self):
        """Player cannot delete a campaign."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)

        response = client.delete(
            f"/api/v1/campaigns/{campaign['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 403


class TestCampaignJoin:
    """Tests for joining campaigns."""

    def test_player_can_add_own_character(self):
        """Player can add their own character to a campaign."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)
        char = create_character(player_token)

        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/join/{char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        assert "joined campaign" in response.json()["message"]

    def test_dm_can_add_any_character(self):
        """DM can add any character to a campaign."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)
        char = create_character(player_token)

        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/join/{char['id']}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )
        assert response.status_code == 200

    def test_cannot_add_others_character(self):
        """Player cannot add another player's character."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)
        # Create character owned by DM
        dm_char = create_character(dm_token, "DM Character")

        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/join/{dm_char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 403


class TestCampaignLeave:
    """Tests for leaving campaigns."""

    def test_player_can_remove_own_character(self):
        """Player can remove their character from a campaign."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)
        char = create_character(player_token)

        # Join first
        client.post(
            f"/api/v1/campaigns/{campaign['id']}/join/{char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        # Then leave
        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/leave/{char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        assert "left the campaign" in response.json()["message"]

    def test_leave_wrong_campaign_fails(self):
        """Cannot leave a campaign the character isn't in."""
        dm_token = create_user("testdm", "dm@test.com", is_dm=True)
        player_token = create_user("testplayer", "player@test.com", is_dm=False)

        campaign = create_campaign_db(dm_token)
        char = create_character(player_token)

        response = client.post(
            f"/api/v1/campaigns/{campaign['id']}/leave/{char['id']}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 400
        assert "not in this campaign" in response.json()["detail"]
