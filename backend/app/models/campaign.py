from app.core.database import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Campaign(Base):
    """Campaign model for organizing game sessions."""

    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    dm_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic Info
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Legacy field - keeping for backwards compatibility but maps are now in separate table
    maps_legacy = Column(JSON, default=list, nullable=False)

    # Campaign settings
    settings = Column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    dm = relationship("User", back_populates="campaigns")
    characters = relationship("Character", back_populates="campaign", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="campaign", cascade="all, delete-orphan")
    maps = relationship("Map", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Campaign(id={self.id}, name={self.name}, dm_id={self.dm_id})>"
