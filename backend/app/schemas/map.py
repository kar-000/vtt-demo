from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MapToken(BaseModel):
    """Schema for a token on the map."""

    id: str  # Unique ID for the token (client-generated UUID)
    name: str
    x: int  # Grid x coordinate
    y: int  # Grid y coordinate
    size: int = Field(default=1, ge=1, le=4)  # Size in grid squares (1=medium, 2=large, etc.)
    color: str = Field(default="#3498db")
    character_id: Optional[int] = None  # If linked to a player character
    combatant_id: Optional[str] = None  # If linked to a combatant in initiative


class RevealedCell(BaseModel):
    """Schema for a revealed fog of war cell."""

    x: int
    y: int


class MapBase(BaseModel):
    """Base map schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    grid_size: int = Field(default=40, ge=20, le=100)
    grid_width: int = Field(default=20, ge=5, le=100)
    grid_height: int = Field(default=15, ge=5, le=100)
    show_grid: bool = Field(default=True)
    grid_color: str = Field(default="rgba(255, 255, 255, 0.3)")
    fog_enabled: bool = Field(default=False)


class MapCreate(MapBase):
    """Schema for map creation."""

    campaign_id: int
    image_data: Optional[str] = None  # Base64 encoded image


class MapUpdate(BaseModel):
    """Schema for map updates."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_data: Optional[str] = None
    grid_size: Optional[int] = Field(None, ge=20, le=100)
    grid_width: Optional[int] = Field(None, ge=5, le=100)
    grid_height: Optional[int] = Field(None, ge=5, le=100)
    show_grid: Optional[bool] = None
    grid_color: Optional[str] = None
    fog_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class TokenUpdate(BaseModel):
    """Schema for updating tokens on a map."""

    tokens: List[MapToken]


class TokenMove(BaseModel):
    """Schema for moving a single token."""

    token_id: str
    x: int
    y: int


class FogUpdate(BaseModel):
    """Schema for updating fog of war."""

    revealed_cells: List[RevealedCell]
    action: str = Field(default="set")  # set, add, remove


class MapResponse(MapBase):
    """Schema for map response."""

    id: int
    campaign_id: int
    image_data: Optional[str] = None
    tokens: List[MapToken] = Field(default_factory=list)
    revealed_cells: List[RevealedCell] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class MapListResponse(BaseModel):
    """Schema for map list response (without image data to reduce payload)."""

    id: int
    campaign_id: int
    name: str
    description: Optional[str] = None
    grid_width: int
    grid_height: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
