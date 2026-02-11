from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base note schema."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")
    note_type: str = Field(default="session_note")
    is_public: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    """Schema for note creation."""

    campaign_id: int


class NoteUpdate(BaseModel):
    """Schema for note updates."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    note_type: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class NoteResponse(NoteBase):
    """Schema for note response."""

    id: int
    campaign_id: int
    user_id: int
    author_username: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
