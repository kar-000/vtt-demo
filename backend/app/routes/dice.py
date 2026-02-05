from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
import random
import logging

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.dice import DiceRoll, DiceRollResult
from app.websocket.manager import manager

router = APIRouter(tags=["Dice"])
logger = logging.getLogger(__name__)


def roll_dice(num_dice: int, dice_type: int) -> list[int]:
    """Roll dice and return individual results."""
    return [random.randint(1, dice_type) for _ in range(num_dice)]


@router.websocket("/ws/game/{campaign_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    campaign_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time game updates."""
    # Authenticate user from token
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)  # Policy violation
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008)
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        await websocket.close(code=1008)
        return

    # Connect to WebSocket manager
    await manager.connect(websocket, campaign_id, user.id, user.username)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "dice_roll":
                # Handle dice roll
                roll_data = data.get("data", {})

                # Validate dice type
                valid_dice = [4, 6, 8, 10, 12, 20, 100]
                dice_type = roll_data.get("dice_type")
                if dice_type not in valid_dice:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Invalid dice type"},
                        websocket,
                    )
                    continue

                # Perform roll
                num_dice = roll_data.get("num_dice", 1)
                modifier = roll_data.get("modifier", 0)
                rolls = roll_dice(num_dice, dice_type)
                total = sum(rolls) + modifier

                # Create result
                result = {
                    "type": "dice_roll_result",
                    "data": {
                        "character_name": roll_data.get("character_name", user.username),
                        "dice_type": dice_type,
                        "num_dice": num_dice,
                        "rolls": rolls,
                        "modifier": modifier,
                        "total": total,
                        "roll_type": roll_data.get("roll_type", "manual"),
                        "label": roll_data.get("label"),
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_id": user.id,
                        "username": user.username,
                    },
                }

                # Broadcast to all users in the campaign
                await manager.broadcast_to_campaign(campaign_id, result)

            elif message_type == "chat_message":
                # Handle chat messages (for future use)
                message = {
                    "type": "chat_message",
                    "data": {
                        "username": user.username,
                        "message": data.get("message", ""),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
                await manager.broadcast_to_campaign(campaign_id, message)

            else:
                # Unknown message type
                await manager.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {message_type}"},
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Notify others that user disconnected
        await manager.broadcast_to_campaign(
            campaign_id,
            {
                "type": "user_disconnected",
                "username": user.username,
                "user_id": user.id,
            },
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
