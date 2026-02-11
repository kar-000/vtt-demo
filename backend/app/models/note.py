from app.core.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Note(Base):
    """Note model for campaign notes and character journals."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False, default="")

    # Type: session_note, character_journal, dm_note
    note_type = Column(String, default="session_note")

    # Visibility: True = visible to all players, False = only author and DM
    is_public = Column(Boolean, default=False)

    # Tags for organization and search (JSON array)
    tags = Column(JSON, default=list, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="notes")
    author = relationship("User", back_populates="notes")

    def __repr__(self):
        return f"<Note(id={self.id}, title={self.title}, author_id={self.user_id})>"
