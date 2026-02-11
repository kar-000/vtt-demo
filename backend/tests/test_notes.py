"""Tests for campaign notes functionality."""

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


def create_campaign(token, name="Test Campaign"):
    """Helper to create a campaign. Returns campaign id."""
    # We need to create a campaign via the database directly since there's no endpoint
    # For now, we'll use campaign_id = 1 in tests after creating it
    from app.models.campaign import Campaign
    from app.models.user import User

    db = TestingSessionLocal()
    try:
        # Get user id from token
        from app.core.security import decode_access_token

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


class TestNotesCRUD:
    """Tests for basic notes CRUD operations."""

    def test_create_note(self):
        """User can create a note in a campaign."""
        token = create_user("player1", "player1@example.com")
        campaign_id = create_campaign(token)

        response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Session 1 Notes",
                "content": "We fought goblins today.",
                "note_type": "session_note",
                "is_public": True,
                "tags": ["combat", "goblins"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Session 1 Notes"
        assert data["content"] == "We fought goblins today."
        assert data["is_public"] is True
        assert "combat" in data["tags"]
        assert data["author_username"] == "player1"

    def test_get_note(self):
        """User can retrieve a specific note."""
        token = create_user("player1", "player1@example.com")
        campaign_id = create_campaign(token)

        # Create a note
        create_response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": campaign_id,
                "title": "My Note",
                "content": "Note content",
            },
        )
        note_id = create_response.json()["id"]

        # Retrieve it
        response = client.get(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "My Note"

    def test_update_note(self):
        """User can update their own note."""
        token = create_user("player1", "player1@example.com")
        campaign_id = create_campaign(token)

        # Create a note
        create_response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Original Title",
                "content": "Original content",
            },
        )
        note_id = create_response.json()["id"]

        # Update it
        response = client.put(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Updated Title", "content": "Updated content"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        assert response.json()["content"] == "Updated content"

    def test_delete_note(self):
        """User can delete their own note."""
        token = create_user("player1", "player1@example.com")
        campaign_id = create_campaign(token)

        # Create a note
        create_response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": campaign_id,
                "title": "To Delete",
                "content": "Will be deleted",
            },
        )
        note_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404


class TestNotesVisibility:
    """Tests for note visibility and access control."""

    def test_player_sees_own_notes(self):
        """Player can see their own notes in campaign."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player_token = create_user("player1", "player1@example.com")

        # Player creates a private note
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "My Private Note",
                "content": "Secret stuff",
                "is_public": False,
            },
        )

        # Player lists campaign notes
        response = client.get(
            f"/api/v1/notes/campaign/{campaign_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 1
        assert notes[0]["title"] == "My Private Note"

    def test_player_sees_public_notes(self):
        """Player can see other players' public notes."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player1_token = create_user("player1", "player1@example.com")
        player2_token = create_user("player2", "player2@example.com")

        # Player 1 creates a public note
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player1_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Public Note",
                "content": "Everyone can see this",
                "is_public": True,
            },
        )

        # Player 2 lists campaign notes
        response = client.get(
            f"/api/v1/notes/campaign/{campaign_id}",
            headers={"Authorization": f"Bearer {player2_token}"},
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 1
        assert notes[0]["title"] == "Public Note"

    def test_player_cannot_see_others_private_notes(self):
        """Player cannot see other players' private notes."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player1_token = create_user("player1", "player1@example.com")
        player2_token = create_user("player2", "player2@example.com")

        # Player 1 creates a private note
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player1_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Private Note",
                "content": "Player 2 cannot see this",
                "is_public": False,
            },
        )

        # Player 2 lists campaign notes
        response = client.get(
            f"/api/v1/notes/campaign/{campaign_id}",
            headers={"Authorization": f"Bearer {player2_token}"},
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 0

    def test_dm_sees_all_notes(self):
        """DM can see all notes including private ones."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player_token = create_user("player1", "player1@example.com")

        # Player creates a private note
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Player Private Note",
                "content": "DM can still see this",
                "is_public": False,
            },
        )

        # DM lists campaign notes
        response = client.get(
            f"/api/v1/notes/campaign/{campaign_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 1
        assert notes[0]["title"] == "Player Private Note"


class TestNotesAuthorization:
    """Tests for note authorization rules."""

    def test_cannot_update_others_note(self):
        """User cannot update another user's note."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player1_token = create_user("player1", "player1@example.com")
        player2_token = create_user("player2", "player2@example.com")

        # Player 1 creates a public note
        create_response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player1_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Player 1 Note",
                "is_public": True,
            },
        )
        note_id = create_response.json()["id"]

        # Player 2 tries to update it
        response = client.put(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {player2_token}"},
            json={"title": "Hacked Title"},
        )

        assert response.status_code == 403

    def test_player_cannot_delete_others_note(self):
        """Player cannot delete another player's note."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player1_token = create_user("player1", "player1@example.com")
        player2_token = create_user("player2", "player2@example.com")

        # Player 1 creates a note
        create_response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player1_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Player 1 Note",
                "is_public": True,
            },
        )
        note_id = create_response.json()["id"]

        # Player 2 tries to delete it
        response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {player2_token}"},
        )

        assert response.status_code == 403

    def test_dm_can_delete_any_note(self):
        """DM can delete any note in the campaign."""
        dm_token = create_user("dm_user", "dm@example.com", is_dm=True)
        campaign_id = create_campaign(dm_token)

        player_token = create_user("player1", "player1@example.com")

        # Player creates a note
        create_response = client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {player_token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Player Note",
                "is_public": False,
            },
        )
        note_id = create_response.json()["id"]

        # DM deletes it
        response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        assert response.status_code == 204


class TestNotesFiltering:
    """Tests for note filtering functionality."""

    def test_filter_by_note_type(self):
        """Notes can be filtered by type."""
        token = create_user("player1", "player1@example.com")
        campaign_id = create_campaign(token)

        # Create notes of different types
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Session Note",
                "note_type": "session_note",
            },
        )
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "campaign_id": campaign_id,
                "title": "Journal Entry",
                "note_type": "character_journal",
            },
        )

        # Filter by session_note
        response = client.get(
            f"/api/v1/notes/campaign/{campaign_id}?note_type=session_note",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 1
        assert notes[0]["title"] == "Session Note"

    def test_list_my_notes(self):
        """User can list all their notes across campaigns."""
        token = create_user("player1", "player1@example.com")
        campaign1_id = create_campaign(token, "Campaign 1")
        campaign2_id = create_campaign(token, "Campaign 2")

        # Create notes in different campaigns
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={"campaign_id": campaign1_id, "title": "Note in C1"},
        )
        client.post(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
            json={"campaign_id": campaign2_id, "title": "Note in C2"},
        )

        # Get all my notes
        response = client.get(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 2
