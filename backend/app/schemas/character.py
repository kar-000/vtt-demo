from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class CharacterBase(BaseModel):
    """Base character schema."""
    name: str = Field(..., min_length=1, max_length=100)
    race: str
    character_class: str
    level: int = Field(default=1, ge=1, le=20)
    avatar_url: Optional[str] = None
    background: Optional[str] = None
    alignment: Optional[str] = None

    # Core Stats
    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)

    # Derived Stats
    armor_class: int = Field(default=10, ge=1)
    max_hp: int = Field(default=10, ge=1)
    current_hp: int = Field(default=10, ge=0)
    temp_hp: int = Field(default=0, ge=0)
    speed: int = Field(default=30, ge=0)
    initiative_bonus: int = Field(default=0)


class CharacterCreate(CharacterBase):
    """Schema for character creation."""
    campaign_id: Optional[int] = None
    proficiencies: Optional[Dict[str, List[str]]] = None
    saving_throw_proficiencies: Optional[Dict[str, bool]] = None
    skills: Optional[Dict[str, int]] = None


class CharacterUpdate(BaseModel):
    """Schema for character updates."""
    name: Optional[str] = None
    race: Optional[str] = None
    character_class: Optional[str] = None
    level: Optional[int] = Field(None, ge=1, le=20)
    avatar_url: Optional[str] = None
    background: Optional[str] = None
    alignment: Optional[str] = None

    strength: Optional[int] = Field(None, ge=1, le=30)
    dexterity: Optional[int] = Field(None, ge=1, le=30)
    constitution: Optional[int] = Field(None, ge=1, le=30)
    intelligence: Optional[int] = Field(None, ge=1, le=30)
    wisdom: Optional[int] = Field(None, ge=1, le=30)
    charisma: Optional[int] = Field(None, ge=1, le=30)

    armor_class: Optional[int] = Field(None, ge=1)
    max_hp: Optional[int] = Field(None, ge=1)
    current_hp: Optional[int] = Field(None, ge=0)
    temp_hp: Optional[int] = Field(None, ge=0)
    speed: Optional[int] = Field(None, ge=0)
    initiative_bonus: Optional[int] = None

    proficiencies: Optional[Dict[str, List[str]]] = None
    saving_throw_proficiencies: Optional[Dict[str, bool]] = None
    skills: Optional[Dict[str, int]] = None
    attacks: Optional[List[Dict[str, Any]]] = None
    spells: Optional[Dict[str, Any]] = None
    features: Optional[List[Dict[str, str]]] = None
    equipment: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None


class CharacterResponse(CharacterBase):
    """Schema for character response."""
    id: int
    owner_id: int
    campaign_id: Optional[int]
    proficiencies: Dict[str, List[str]]
    saving_throw_proficiencies: Dict[str, bool]
    skills: Dict[str, int]
    attacks: List[Dict[str, Any]]
    spells: Dict[str, Any]
    features: List[Dict[str, str]]
    equipment: List[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Computed properties
    proficiency_bonus: int
    strength_modifier: int
    dexterity_modifier: int
    constitution_modifier: int
    intelligence_modifier: int
    wisdom_modifier: int
    charisma_modifier: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to include computed properties."""
        data = {
            **{c.name: getattr(obj, c.name) for c in obj.__table__.columns},
            "proficiency_bonus": obj.proficiency_bonus,
            "strength_modifier": obj.strength_modifier,
            "dexterity_modifier": obj.dexterity_modifier,
            "constitution_modifier": obj.constitution_modifier,
            "intelligence_modifier": obj.intelligence_modifier,
            "wisdom_modifier": obj.wisdom_modifier,
            "charisma_modifier": obj.charisma_modifier,
        }
        return cls(**data)
