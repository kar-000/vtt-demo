"""Pydantic schemas for Campaign."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    """Schema for creating a new campaign."""

    name: str
    description: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""

    name: Optional[str] = None
    description: Optional[str] = None


class CampaignResponse(BaseModel):
    """Schema for campaign response."""

    id: int
    dm_id: int
    name: str
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        """Pydantic configuration."""

        orm_mode = True


class CampaignListResponse(BaseModel):
    """Schema for listing campaigns."""

    id: int
    dm_id: int
    name: str
    description: Optional[str]
    character_count: int = 0

    class Config:
        """Pydantic configuration."""

        orm_mode = True
