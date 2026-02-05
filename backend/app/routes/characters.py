from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse

router = APIRouter(prefix="/characters", tags=["Characters"])


@router.post("/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new character."""
    # Initialize default values for JSON fields
    proficiencies = character_data.proficiencies or {
        "armor": [],
        "weapons": [],
        "tools": [],
        "languages": [],
    }

    saving_throw_proficiencies = character_data.saving_throw_proficiencies or {
        "strength": False,
        "dexterity": False,
        "constitution": False,
        "intelligence": False,
        "wisdom": False,
        "charisma": False,
    }

    skills = character_data.skills or {
        "acrobatics": 0,
        "animal_handling": 0,
        "arcana": 0,
        "athletics": 0,
        "deception": 0,
        "history": 0,
        "insight": 0,
        "intimidation": 0,
        "investigation": 0,
        "medicine": 0,
        "nature": 0,
        "perception": 0,
        "performance": 0,
        "persuasion": 0,
        "religion": 0,
        "sleight_of_hand": 0,
        "stealth": 0,
        "survival": 0,
    }

    # Create character
    new_character = Character(
        owner_id=current_user.id,
        name=character_data.name,
        race=character_data.race,
        character_class=character_data.character_class,
        level=character_data.level,
        avatar_url=character_data.avatar_url,
        background=character_data.background,
        alignment=character_data.alignment,
        strength=character_data.strength,
        dexterity=character_data.dexterity,
        constitution=character_data.constitution,
        intelligence=character_data.intelligence,
        wisdom=character_data.wisdom,
        charisma=character_data.charisma,
        armor_class=character_data.armor_class,
        max_hp=character_data.max_hp,
        current_hp=character_data.current_hp,
        temp_hp=character_data.temp_hp,
        speed=character_data.speed,
        initiative_bonus=character_data.initiative_bonus,
        proficiencies=proficiencies,
        saving_throw_proficiencies=saving_throw_proficiencies,
        skills=skills,
        campaign_id=character_data.campaign_id,
    )

    db.add(new_character)
    db.commit()
    db.refresh(new_character)

    return CharacterResponse.from_orm(new_character)


@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all characters owned by the current user."""
    characters = (
        db.query(Character)
        .filter(Character.owner_id == current_user.id)
        .order_by(Character.created_at.desc())
        .all()
    )

    return [CharacterResponse.from_orm(char) for char in characters]


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific character by ID."""
    character = db.query(Character).filter(Character.id == character_id).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    # Check if user owns the character or is a DM
    if character.owner_id != current_user.id and not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this character",
        )

    return CharacterResponse.from_orm(character)


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    character_data: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a character."""
    character = db.query(Character).filter(Character.id == character_id).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    # Check if user owns the character
    if character.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this character",
        )

    # Update fields
    update_data = character_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    db.commit()
    db.refresh(character)

    return CharacterResponse.from_orm(character)


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a character."""
    character = db.query(Character).filter(Character.id == character_id).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    # Check if user owns the character
    if character.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this character",
        )

    db.delete(character)
    db.commit()

    return None
