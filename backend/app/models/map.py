from app.core.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Map(Base):
    """Battle map model for tactical combat visualization."""

    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)

    # Map metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Image data (base64 encoded)
    image_data = Column(Text, nullable=True)

    # Grid configuration
    grid_size = Column(Integer, default=40)  # Pixels per square
    grid_width = Column(Integer, default=20)  # Number of squares wide
    grid_height = Column(Integer, default=15)  # Number of squares tall
    show_grid = Column(Boolean, default=True)
    grid_color = Column(String, default="rgba(255, 255, 255, 0.3)")

    # Tokens on the map (JSON array of token objects)
    # Each token: {id, name, x, y, size, color, character_id?, combatant_id?}
    tokens = Column(JSON, default=list, nullable=False)

    # Fog of war (JSON array of revealed cell coordinates)
    # Each cell: {x, y}
    revealed_cells = Column(JSON, default=list, nullable=False)
    fog_enabled = Column(Boolean, default=False)

    # Active state - only one map active per campaign at a time
    is_active = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="maps")

    def __repr__(self):
        return f"<Map(id={self.id}, name={self.name}, campaign_id={self.campaign_id})>"
