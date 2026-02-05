from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DiceRoll(BaseModel):
    """Schema for a dice roll request."""

    character_name: str
    dice_type: int = Field(..., description="Type of dice (4, 6, 8, 10, 12, 20, 100)")
    num_dice: int = Field(default=1, ge=1, le=100, description="Number of dice to roll")
    modifier: int = Field(default=0, description="Modifier to add to the roll")
    roll_type: str = Field(default="manual", description="Type of roll (manual, ability, skill, save, attack)")
    label: Optional[str] = Field(None, description="Label for the roll (e.g., 'Strength Check', 'Longsword Attack')")


class DiceRollResult(BaseModel):
    """Schema for a dice roll result."""

    character_name: str
    dice_type: int
    num_dice: int
    rolls: List[int]
    modifier: int
    total: int
    roll_type: str
    label: Optional[str] = None
    timestamp: datetime

    class Config:
        orm_mode = True
