"""Campaign routes for campaign management."""

from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.campaign import Campaign
from app.models.character import Character
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignListResponse, CampaignResponse, CampaignUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new campaign. Only DMs can create campaigns."""
    if not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only DMs can create campaigns",
        )

    campaign = Campaign(
        dm_id=current_user.id,
        name=campaign_data.name,
        description=campaign_data.description,
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return CampaignResponse.from_orm(campaign)


@router.get("/", response_model=List[CampaignListResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all campaigns. DMs see all campaigns, players see campaigns they're in."""
    if current_user.is_dm:
        campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    else:
        # Get campaigns where the user has a character
        campaign_ids = (
            db.query(Character.campaign_id)
            .filter(Character.owner_id == current_user.id)
            .filter(Character.campaign_id.isnot(None))
            .distinct()
            .all()
        )
        campaign_ids = [cid[0] for cid in campaign_ids]
        campaigns = db.query(Campaign).filter(Campaign.id.in_(campaign_ids)).order_by(Campaign.created_at.desc()).all()

    # Count characters per campaign
    result = []
    for campaign in campaigns:
        char_count = db.query(Character).filter(Character.campaign_id == campaign.id).count()
        result.append(
            CampaignListResponse(
                id=campaign.id,
                dm_id=campaign.dm_id,
                name=campaign.name,
                description=campaign.description,
                character_count=char_count,
            )
        )

    return result


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific campaign by ID."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    # Check access: DM or player with character in campaign
    if not current_user.is_dm:
        has_character = (
            db.query(Character).filter(Character.campaign_id == campaign_id, Character.owner_id == current_user.id).first()
        )
        if not has_character:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this campaign",
            )

    return CampaignResponse.from_orm(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a campaign. Only the DM who owns the campaign can update it."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    if campaign.dm_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the campaign DM can update this campaign",
        )

    update_data = campaign_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    db.commit()
    db.refresh(campaign)

    return CampaignResponse.from_orm(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a campaign. Only the DM who owns the campaign can delete it."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    if campaign.dm_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the campaign DM can delete this campaign",
        )

    db.delete(campaign)
    db.commit()

    return None


@router.post("/{campaign_id}/join/{character_id}", response_model=dict)
async def join_campaign(
    campaign_id: int,
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a character to a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    character = db.query(Character).filter(Character.id == character_id).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    # Check ownership: must own the character or be DM
    if character.owner_id != current_user.id and not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add this character to a campaign",
        )

    character.campaign_id = campaign_id
    db.commit()

    return {"message": f"Character {character.name} joined campaign {campaign.name}"}


@router.post("/{campaign_id}/leave/{character_id}", response_model=dict)
async def leave_campaign(
    campaign_id: int,
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a character from a campaign."""
    character = db.query(Character).filter(Character.id == character_id).first()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    if character.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character is not in this campaign",
        )

    # Check ownership: must own the character or be DM
    if character.owner_id != current_user.id and not current_user.is_dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this character from a campaign",
        )

    character.campaign_id = None
    db.commit()

    return {"message": f"Character {character.name} left the campaign"}
