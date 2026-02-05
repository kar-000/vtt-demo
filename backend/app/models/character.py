from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Character(Base):
    """Character model for D&D 5e characters."""

    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Basic Info
    name = Column(String, nullable=False, index=True)
    race = Column(String, nullable=False)
    character_class = Column(String, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    avatar_url = Column(String, nullable=True)
    background = Column(String, nullable=True)
    alignment = Column(String, nullable=True)

    # Core Stats (Ability Scores)
    strength = Column(Integer, default=10, nullable=False)
    dexterity = Column(Integer, default=10, nullable=False)
    constitution = Column(Integer, default=10, nullable=False)
    intelligence = Column(Integer, default=10, nullable=False)
    wisdom = Column(Integer, default=10, nullable=False)
    charisma = Column(Integer, default=10, nullable=False)

    # Derived Stats
    armor_class = Column(Integer, default=10, nullable=False)
    max_hp = Column(Integer, default=10, nullable=False)
    current_hp = Column(Integer, default=10, nullable=False)
    temp_hp = Column(Integer, default=0, nullable=False)
    speed = Column(Integer, default=30, nullable=False)
    initiative_bonus = Column(Integer, default=0, nullable=False)

    # Proficiencies (stored as JSON for flexibility)
    # Structure: {"armor": [], "weapons": [], "tools": [], "languages": []}
    proficiencies = Column(JSON, default=dict, nullable=False)

    # Saving Throw Proficiencies (stored as JSON)
    # Structure: {"strength": false, "dexterity": true, ...}
    saving_throw_proficiencies = Column(JSON, default=dict, nullable=False)

    # Skills (stored as JSON with proficiency level)
    # Structure: {"acrobatics": 0, "athletics": 1, "perception": 2, ...}
    # 0 = not proficient, 1 = proficient, 2 = expert
    skills = Column(JSON, default=dict, nullable=False)

    # Phase 2+ Features (prepared for future expansion)
    # Attacks will be stored as JSON
    # Structure: [{"name": "Longsword", "bonus": 5, "damage_dice": "1d8", "damage_type": "slashing"}]
    attacks = Column(JSON, default=list, nullable=False)

    # Spells will be stored as JSON
    # Structure: {"spell_slots": {...}, "spells_known": [...], "spell_save_dc": 0, "spell_attack_bonus": 0}
    spells = Column(JSON, default=dict, nullable=False)

    # Abilities and Features (class features, racial traits, feats)
    # Structure: [{"name": "...", "description": "...", "source": "class/race/feat"}]
    features = Column(JSON, default=list, nullable=False)

    # Equipment and Inventory
    equipment = Column(JSON, default=list, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="characters")
    campaign = relationship("Campaign", back_populates="characters")

    def __repr__(self):
        return f"<Character(id={self.id}, name={self.name}, class={self.character_class}, level={self.level})>"

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level."""
        return 2 + ((self.level - 1) // 4)

    def get_ability_modifier(self, ability_score: int) -> int:
        """Calculate ability modifier from ability score."""
        return (ability_score - 10) // 2

    @property
    def strength_modifier(self) -> int:
        return self.get_ability_modifier(self.strength)

    @property
    def dexterity_modifier(self) -> int:
        return self.get_ability_modifier(self.dexterity)

    @property
    def constitution_modifier(self) -> int:
        return self.get_ability_modifier(self.constitution)

    @property
    def intelligence_modifier(self) -> int:
        return self.get_ability_modifier(self.intelligence)

    @property
    def wisdom_modifier(self) -> int:
        return self.get_ability_modifier(self.wisdom)

    @property
    def charisma_modifier(self) -> int:
        return self.get_ability_modifier(self.charisma)
