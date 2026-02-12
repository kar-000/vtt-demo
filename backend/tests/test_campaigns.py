"""Tests for campaign endpoints."""

import pytest
from app.core.database import Base, engine, get_db
from app.main import app
from app.models.campaign import Campaign
from app.models.character import Character
from app.models.user import User
from app.routes.auth import pwd_context
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def dm_user(test_db):
    """Create a DM user and return auth token."""
    db = next(get_db())
    user = User(
        username="testdm",
        email="dm@test.com",
        hashed_password=pwd_context.hash("testpass123"),
        is_dm=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testdm", "password": "testpass123"},
    )
    return {"token": response.json()["access_token"], "user": user}


@pytest.fixture
def player_user(test_db):
    """Create a player user and return auth token."""
    db = next(get_db())
    user = User(
        username="testplayer",
        email="player@test.com",
        hashed_password=pwd_context.hash("testpass123"),
        is_dm=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testplayer", "password": "testpass123"},
    )
    return {"token": response.json()["access_token"], "user": user}


@pytest.fixture
def test_campaign(test_db, dm_user):
    """Create a test campaign."""
    db = next(get_db())
    campaign = Campaign(
        dm_id=dm_user["user"].id,
        name="Test Campaign",
        description="A test campaign",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    db.close()
    return campaign


@pytest.fixture
def test_character(test_db, player_user):
    """Create a test character."""
    db = next(get_db())
    character = Character(
        owner_id=player_user["user"].id,
        name="Test Character",
        race="Human",
        character_class="Fighter",
        level=1,
        strength=16,
        dexterity=14,
        constitution=15,
        intelligence=10,
        wisdom=12,
        charisma=8,
        max_hp=12,
        current_hp=12,
        armor_class=16,
        speed=30,
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    db.close()
    return character


class TestCampaignCreate:
    """Tests for creating campaigns."""

    def test_create_campaign_as_dm(self, client, dm_user):
        """DM can create a campaign."""
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "New Campaign", "description": "An epic adventure"},
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Campaign"
        assert data["description"] == "An epic adventure"
        assert data["dm_id"] == dm_user["user"].id

    def test_create_campaign_without_description(self, client, dm_user):
        """DM can create a campaign without description."""
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "Minimal Campaign"},
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Campaign"
        assert data["description"] is None

    def test_create_campaign_as_player_fails(self, client, player_user):
        """Players cannot create campaigns."""
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "Player Campaign"},
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 403
        assert "Only DMs can create campaigns" in response.json()["detail"]

    def test_create_campaign_unauthenticated_fails(self, client, test_db):
        """Unauthenticated users cannot create campaigns."""
        response = client.post(
            "/api/v1/campaigns/",
            json={"name": "Unauthorized Campaign"},
        )
        assert response.status_code == 401


class TestCampaignList:
    """Tests for listing campaigns."""

    def test_dm_sees_all_campaigns(self, client, dm_user, test_campaign):
        """DM can see all campaigns."""
        response = client.get(
            "/api/v1/campaigns/",
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(c["name"] == "Test Campaign" for c in data)

    def test_player_sees_own_campaigns(self, client, player_user, test_campaign, test_character):
        """Player only sees campaigns they're in."""
        # First, add character to campaign
        db = next(get_db())
        char = db.query(Character).filter(Character.id == test_character.id).first()
        char.campaign_id = test_campaign.id
        db.commit()
        db.close()

        response = client.get(
            "/api/v1/campaigns/",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Campaign"

    def test_player_without_campaign_sees_empty(self, client, player_user, test_campaign):
        """Player without campaign sees empty list."""
        response = client.get(
            "/api/v1/campaigns/",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestCampaignGet:
    """Tests for getting a specific campaign."""

    def test_dm_can_get_campaign(self, client, dm_user, test_campaign):
        """DM can get any campaign."""
        response = client.get(
            f"/api/v1/campaigns/{test_campaign.id}",
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Campaign"

    def test_player_in_campaign_can_get(self, client, player_user, test_campaign, test_character):
        """Player with character in campaign can get it."""
        db = next(get_db())
        char = db.query(Character).filter(Character.id == test_character.id).first()
        char.campaign_id = test_campaign.id
        db.commit()
        db.close()

        response = client.get(
            f"/api/v1/campaigns/{test_campaign.id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 200

    def test_player_not_in_campaign_denied(self, client, player_user, test_campaign):
        """Player without character in campaign is denied."""
        response = client.get(
            f"/api/v1/campaigns/{test_campaign.id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 403

    def test_nonexistent_campaign_404(self, client, dm_user):
        """Nonexistent campaign returns 404."""
        response = client.get(
            "/api/v1/campaigns/99999",
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 404


class TestCampaignUpdate:
    """Tests for updating campaigns."""

    def test_dm_can_update_own_campaign(self, client, dm_user, test_campaign):
        """DM can update their own campaign."""
        response = client.put(
            f"/api/v1/campaigns/{test_campaign.id}",
            json={"name": "Updated Campaign", "description": "New description"},
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign"
        assert data["description"] == "New description"

    def test_other_dm_cannot_update(self, client, test_campaign, test_db):
        """Another DM cannot update the campaign."""
        # Create another DM
        db = next(get_db())
        user = User(
            username="otherdm",
            email="other@test.com",
            hashed_password=pwd_context.hash("testpass123"),
            is_dm=True,
        )
        db.add(user)
        db.commit()
        db.close()

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "otherdm", "password": "testpass123"},
        )
        other_token = login_response.json()["access_token"]

        response = client.put(
            f"/api/v1/campaigns/{test_campaign.id}",
            json={"name": "Hijacked"},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert response.status_code == 403


class TestCampaignDelete:
    """Tests for deleting campaigns."""

    def test_dm_can_delete_own_campaign(self, client, dm_user, test_campaign):
        """DM can delete their own campaign."""
        response = client.delete(
            f"/api/v1/campaigns/{test_campaign.id}",
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(
            f"/api/v1/campaigns/{test_campaign.id}",
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 404

    def test_player_cannot_delete_campaign(self, client, player_user, test_campaign):
        """Player cannot delete a campaign."""
        response = client.delete(
            f"/api/v1/campaigns/{test_campaign.id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 403


class TestCampaignJoin:
    """Tests for joining campaigns."""

    def test_player_can_add_own_character(self, client, player_user, test_campaign, test_character):
        """Player can add their own character to a campaign."""
        response = client.post(
            f"/api/v1/campaigns/{test_campaign.id}/join/{test_character.id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 200
        assert "joined campaign" in response.json()["message"]

        # Verify character is in campaign
        db = next(get_db())
        char = db.query(Character).filter(Character.id == test_character.id).first()
        assert char.campaign_id == test_campaign.id
        db.close()

    def test_dm_can_add_any_character(self, client, dm_user, test_campaign, test_character):
        """DM can add any character to a campaign."""
        response = client.post(
            f"/api/v1/campaigns/{test_campaign.id}/join/{test_character.id}",
            headers={"Authorization": f"Bearer {dm_user['token']}"},
        )
        assert response.status_code == 200

    def test_cannot_add_others_character(self, client, dm_user, player_user, test_campaign, test_db):
        """Player cannot add another player's character."""
        # Create a character owned by DM
        db = next(get_db())
        dm_char = Character(
            owner_id=dm_user["user"].id,
            name="DM Character",
            race="Elf",
            character_class="Wizard",
            level=1,
            strength=10,
            dexterity=14,
            constitution=12,
            intelligence=18,
            wisdom=14,
            charisma=10,
            max_hp=8,
            current_hp=8,
            armor_class=12,
            speed=30,
        )
        db.add(dm_char)
        db.commit()
        db.refresh(dm_char)
        char_id = dm_char.id
        db.close()

        response = client.post(
            f"/api/v1/campaigns/{test_campaign.id}/join/{char_id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 403


class TestCampaignLeave:
    """Tests for leaving campaigns."""

    def test_player_can_remove_own_character(self, client, player_user, test_campaign, test_character):
        """Player can remove their character from a campaign."""
        # First add character to campaign
        db = next(get_db())
        char = db.query(Character).filter(Character.id == test_character.id).first()
        char.campaign_id = test_campaign.id
        db.commit()
        db.close()

        response = client.post(
            f"/api/v1/campaigns/{test_campaign.id}/leave/{test_character.id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 200
        assert "left the campaign" in response.json()["message"]

        # Verify character is no longer in campaign
        db = next(get_db())
        char = db.query(Character).filter(Character.id == test_character.id).first()
        assert char.campaign_id is None
        db.close()

    def test_leave_wrong_campaign_fails(self, client, player_user, test_campaign, test_character):
        """Cannot leave a campaign the character isn't in."""
        response = client.post(
            f"/api/v1/campaigns/{test_campaign.id}/leave/{test_character.id}",
            headers={"Authorization": f"Bearer {player_user['token']}"},
        )
        assert response.status_code == 400
        assert "not in this campaign" in response.json()["detail"]
