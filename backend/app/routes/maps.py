from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.campaign import Campaign
from app.models.map import Map
from app.models.user import User
from app.schemas.map import FogUpdate, MapCreate, MapListResponse, MapResponse, MapUpdate, TokenMove, TokenUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter(prefix="/maps", tags=["Maps"])


def map_to_response(map_obj: Map) -> dict:
    """Convert a Map model to response dict."""
    return {
        "id": map_obj.id,
        "campaign_id": map_obj.campaign_id,
        "name": map_obj.name,
        "description": map_obj.description,
        "image_data": map_obj.image_data,
        "grid_size": map_obj.grid_size,
        "grid_width": map_obj.grid_width,
        "grid_height": map_obj.grid_height,
        "show_grid": map_obj.show_grid,
        "grid_color": map_obj.grid_color,
        "tokens": map_obj.tokens or [],
        "revealed_cells": map_obj.revealed_cells or [],
        "fog_enabled": map_obj.fog_enabled,
        "is_active": map_obj.is_active,
        "created_at": map_obj.created_at,
        "updated_at": map_obj.updated_at,
    }


def map_to_list_response(map_obj: Map) -> dict:
    """Convert a Map model to list response dict (without image data)."""
    return {
        "id": map_obj.id,
        "campaign_id": map_obj.campaign_id,
        "name": map_obj.name,
        "description": map_obj.description,
        "grid_width": map_obj.grid_width,
        "grid_height": map_obj.grid_height,
        "is_active": map_obj.is_active,
        "created_at": map_obj.created_at,
        "updated_at": map_obj.updated_at,
    }


@router.post("/", response_model=MapResponse, status_code=status.HTTP_201_CREATED)
async def create_map(
    map_data: MapCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new battle map. Only DM can create maps."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the DM can create maps",
        )

    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == map_data.campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    # Create map
    new_map = Map(
        campaign_id=map_data.campaign_id,
        name=map_data.name,
        description=map_data.description,
        image_data=map_data.image_data,
        grid_size=map_data.grid_size,
        grid_width=map_data.grid_width,
        grid_height=map_data.grid_height,
        show_grid=map_data.show_grid,
        grid_color=map_data.grid_color,
        fog_enabled=map_data.fog_enabled,
        tokens=[],
        revealed_cells=[],
    )

    db.add(new_map)
    db.commit()
    db.refresh(new_map)

    return map_to_response(new_map)


@router.get("/campaign/{campaign_id}", response_model=List[MapListResponse])
async def list_campaign_maps(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all maps in a campaign."""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    maps = db.query(Map).filter(Map.campaign_id == campaign_id).order_by(Map.created_at.desc()).all()

    return [map_to_list_response(m) for m in maps]


@router.get("/campaign/{campaign_id}/active", response_model=MapResponse)
async def get_active_map(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the currently active map for a campaign."""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    active_map = db.query(Map).filter(Map.campaign_id == campaign_id, Map.is_active == True).first()  # noqa: E712

    if not active_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active map in this campaign",
        )

    return map_to_response(active_map)


@router.get("/{map_id}", response_model=MapResponse)
async def get_map(
    map_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific map by ID."""
    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    return map_to_response(map_obj)


@router.put("/{map_id}", response_model=MapResponse)
async def update_map(
    map_id: int,
    map_data: MapUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a map. Only DM can update maps."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the DM can modify maps",
        )

    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    # If setting this map as active, deactivate other maps in the campaign
    if map_data.is_active:
        db.query(Map).filter(Map.campaign_id == map_obj.campaign_id, Map.id != map_id).update({"is_active": False})

    # Update fields
    update_data = map_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(map_obj, field, value)

    db.commit()
    db.refresh(map_obj)

    return map_to_response(map_obj)


@router.delete("/{map_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_map(
    map_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a map. Only DM can delete maps."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the DM can delete maps",
        )

    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    db.delete(map_obj)
    db.commit()

    return None


@router.patch("/{map_id}/tokens", response_model=MapResponse)
async def update_tokens(
    map_id: int,
    token_data: TokenUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update all tokens on a map. Only DM can update tokens."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the DM can modify tokens",
        )

    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    # Convert tokens to dicts
    map_obj.tokens = [t.dict() for t in token_data.tokens]
    flag_modified(map_obj, "tokens")

    db.commit()
    db.refresh(map_obj)

    return map_to_response(map_obj)


@router.patch("/{map_id}/token/move", response_model=MapResponse)
async def move_token(
    map_id: int,
    move_data: TokenMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Move a single token on a map. DM can move any token, players can move their own."""
    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    tokens = map_obj.tokens or []
    token_found = False

    for token in tokens:
        if token.get("id") == move_data.token_id:
            # Check authorization
            if not current_user.is_dm:
                # Players can only move tokens linked to their own characters
                # TODO: Check character ownership when character_id is set
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the DM can move tokens",
                )
            token["x"] = move_data.x
            token["y"] = move_data.y
            token_found = True
            break

    if not token_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    map_obj.tokens = tokens
    flag_modified(map_obj, "tokens")

    db.commit()
    db.refresh(map_obj)

    return map_to_response(map_obj)


@router.patch("/{map_id}/fog", response_model=MapResponse)
async def update_fog(
    map_id: int,
    fog_data: FogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update fog of war. Only DM can update fog."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the DM can modify fog of war",
        )

    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    current_cells = map_obj.revealed_cells or []
    new_cells = [c.dict() for c in fog_data.revealed_cells]

    if fog_data.action == "set":
        map_obj.revealed_cells = new_cells
    elif fog_data.action == "add":
        # Add new cells, avoiding duplicates
        existing = {(c["x"], c["y"]) for c in current_cells}
        for cell in new_cells:
            if (cell["x"], cell["y"]) not in existing:
                current_cells.append(cell)
        map_obj.revealed_cells = current_cells
    elif fog_data.action == "remove":
        # Remove specified cells
        remove_set = {(c["x"], c["y"]) for c in new_cells}
        map_obj.revealed_cells = [c for c in current_cells if (c["x"], c["y"]) not in remove_set]

    flag_modified(map_obj, "revealed_cells")

    db.commit()
    db.refresh(map_obj)

    return map_to_response(map_obj)


@router.post("/{map_id}/activate", response_model=MapResponse)
async def activate_map(
    map_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Activate a map (deactivates any other active map in the campaign). Only DM."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the DM can activate maps",
        )

    map_obj = db.query(Map).filter(Map.id == map_id).first()

    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    # Deactivate all other maps in the campaign
    db.query(Map).filter(Map.campaign_id == map_obj.campaign_id, Map.id != map_id).update({"is_active": False})

    map_obj.is_active = True
    db.commit()
    db.refresh(map_obj)

    return map_to_response(map_obj)
