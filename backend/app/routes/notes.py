from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.campaign import Campaign
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/notes", tags=["Notes"])


def note_to_response(note: Note, db: Session) -> dict:
    """Convert a Note model to response dict with author username."""
    author = db.query(User).filter(User.id == note.user_id).first()
    return {
        "id": note.id,
        "campaign_id": note.campaign_id,
        "user_id": note.user_id,
        "author_username": author.username if author else None,
        "title": note.title,
        "content": note.content,
        "note_type": note.note_type,
        "is_public": note.is_public,
        "tags": note.tags or [],
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new note in a campaign."""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == note_data.campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    # Create note
    new_note = Note(
        campaign_id=note_data.campaign_id,
        user_id=current_user.id,
        title=note_data.title,
        content=note_data.content,
        note_type=note_data.note_type,
        is_public=note_data.is_public,
        tags=note_data.tags,
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return note_to_response(new_note, db)


@router.get("/campaign/{campaign_id}", response_model=List[NoteResponse])
async def list_campaign_notes(
    campaign_id: int,
    note_type: Optional[str] = Query(None, description="Filter by note type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notes in a campaign visible to the current user."""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    # Build query - user sees their own notes plus public notes
    # DM sees all notes in the campaign
    query = db.query(Note).filter(Note.campaign_id == campaign_id)

    if not current_user.is_dm:
        # Non-DM: see own notes + public notes
        query = query.filter((Note.user_id == current_user.id) | (Note.is_public == True))  # noqa: E712

    # Apply filters
    if note_type:
        query = query.filter(Note.note_type == note_type)

    # Tag filtering (check if tag is in the tags JSON array)
    if tag:
        query = query.filter(Note.tags.contains([tag]))

    notes = query.order_by(Note.created_at.desc()).all()

    return [note_to_response(note, db) for note in notes]


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    # Check access: user owns the note, note is public, or user is DM
    if note.user_id != current_user.id and not note.is_public and not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this note",
        )

    return note_to_response(note, db)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a note."""
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    # Only the author can update their note
    if note.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this note",
        )

    # Update fields
    update_data = note_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)

    return note_to_response(note, db)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a note."""
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    # Only the author or DM can delete a note
    if note.user_id != current_user.id and not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this note",
        )

    db.delete(note)
    db.commit()

    return None


@router.get("/", response_model=List[NoteResponse])
async def list_my_notes(
    note_type: Optional[str] = Query(None, description="Filter by note type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all notes created by the current user across all campaigns."""
    query = db.query(Note).filter(Note.user_id == current_user.id)

    if note_type:
        query = query.filter(Note.note_type == note_type)

    notes = query.order_by(Note.created_at.desc()).all()

    return [note_to_response(note, db) for note in notes]
