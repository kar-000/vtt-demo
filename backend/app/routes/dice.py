import logging
import random
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.campaign import Campaign
from app.models.character import Character
from app.models.user import User
from app.websocket.manager import manager
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

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
                advantage = roll_data.get("advantage")  # None, "advantage", or "disadvantage"

                # Handle advantage/disadvantage for d20 rolls
                if advantage in ("advantage", "disadvantage") and dice_type == 20 and num_dice == 1:
                    roll1 = roll_dice(1, 20)[0]
                    roll2 = roll_dice(1, 20)[0]
                    if advantage == "advantage":
                        used = max(roll1, roll2)
                    else:
                        used = min(roll1, roll2)
                    rolls = [used]
                    all_rolls = [roll1, roll2]
                    total = used + modifier
                else:
                    rolls = roll_dice(num_dice, dice_type)
                    all_rolls = None
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
                        "advantage": advantage,
                        "all_rolls": all_rolls,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "user_id": user.id,
                        "username": user.username,
                    },
                }

                # Broadcast to all users in the campaign
                await manager.broadcast_to_campaign(campaign_id, result)

            elif message_type == "chat_message":
                # Handle chat messages
                chat_data = data.get("data", {})
                message = {
                    "type": "chat_message",
                    "data": {
                        "username": user.username,
                        "message": chat_data.get("message", ""),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    },
                }
                await manager.broadcast_to_campaign(campaign_id, message)

            elif message_type == "initiative_update":
                # Handle initiative tracker updates
                payload = data.get("data", {})
                action = payload.get("action")
                init_data = payload.get("data", {})

                # Get campaign and current initiative state
                campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                if not campaign:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Campaign not found"},
                        websocket,
                    )
                    continue

                # Initialize initiative if not exists
                settings = campaign.settings or {}
                initiative = settings.get(
                    "initiative", {"active": False, "round": 1, "current_turn_index": 0, "combatants": []}
                )

                if action == "start_combat":
                    # Start combat with ALL characters (for multi-player support)
                    all_characters = db.query(Character).all()
                    combatants = []

                    for char in all_characters:
                        combatants.append(
                            {
                                "id": f"char_{char.id}",
                                "name": char.name,
                                "initiative": None,
                                "dex_mod": char.dexterity_modifier,
                                "type": "pc",
                                "character_id": char.id,
                                "action_economy": {
                                    "action": True,
                                    "bonus_action": True,
                                    "reaction": True,
                                    "movement": char.speed or 30,
                                    "max_movement": char.speed or 30,
                                },
                            }
                        )

                    initiative = {"active": True, "round": 1, "current_turn_index": 0, "combatants": combatants}

                elif action == "add_combatant":
                    # Add NPC/monster to initiative with full stat block
                    name = init_data.get("name", "Unknown")
                    init_value = init_data.get("initiative")
                    speed = init_data.get("speed", 30)
                    max_hp = init_data.get("max_hp", 10)
                    armor_class = init_data.get("armor_class", 10)
                    attacks = init_data.get("attacks", [])
                    dex_mod = init_data.get("dex_mod", 0)
                    combatant = {
                        "id": f"npc_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "initiative": init_value,
                        "dex_mod": dex_mod,
                        "type": "npc",
                        "max_hp": max_hp,
                        "current_hp": max_hp,
                        "armor_class": armor_class,
                        "attacks": attacks,
                        "action_economy": {
                            "action": True,
                            "bonus_action": True,
                            "reaction": True,
                            "movement": speed,
                            "max_movement": speed,
                        },
                    }
                    initiative["combatants"].append(combatant)
                    # Re-sort if initiative value provided
                    if init_value is not None:
                        initiative["combatants"] = sorted(
                            initiative["combatants"],
                            key=lambda x: (x["initiative"] or -999, x.get("dex_mod", 0), x["name"]),
                            reverse=True,
                        )

                elif action == "remove_combatant":
                    # Remove combatant by ID
                    combatant_id = init_data.get("combatant_id")
                    initiative["combatants"] = [c for c in initiative["combatants"] if c["id"] != combatant_id]
                    # Adjust current turn index if needed
                    if initiative["current_turn_index"] >= len(initiative["combatants"]):
                        initiative["current_turn_index"] = 0

                elif action == "roll_initiative":
                    # Roll initiative for a specific combatant
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id:
                            roll = random.randint(1, 20)
                            dex_mod = combatant.get("dex_mod", 0)
                            combatant["initiative"] = roll + dex_mod
                            combatant["roll"] = roll
                            break
                    # Re-sort by initiative (desc), then dex_mod (desc), then name (asc)
                    initiative["combatants"] = sorted(
                        initiative["combatants"],
                        key=lambda x: (x["initiative"] or -999, x.get("dex_mod", 0), x["name"]),
                        reverse=True,
                    )
                    # Reset turn index after sorting
                    initiative["current_turn_index"] = 0

                elif action == "set_initiative":
                    # Manually set initiative value
                    combatant_id = init_data.get("combatant_id")
                    value = init_data.get("value")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id:
                            combatant["initiative"] = value
                            break
                    # Re-sort
                    initiative["combatants"] = sorted(
                        initiative["combatants"],
                        key=lambda x: (x["initiative"] or -999, x.get("dex_mod", 0), x["name"]),
                        reverse=True,
                    )

                elif action == "next_turn":
                    # Advance to next turn
                    if initiative["combatants"]:
                        initiative["current_turn_index"] += 1
                        if initiative["current_turn_index"] >= len(initiative["combatants"]):
                            initiative["current_turn_index"] = 0
                            initiative["round"] += 1
                        # Reset action economy for the new current combatant
                        current = initiative["combatants"][initiative["current_turn_index"]]
                        if "action_economy" in current:
                            current["action_economy"]["action"] = True
                            current["action_economy"]["bonus_action"] = True
                            current["action_economy"]["movement"] = current["action_economy"].get("max_movement", 30)
                            # Note: Reaction resets at start of YOUR next turn, not when others' turns change
                            current["action_economy"]["reaction"] = True
                        # Tick down condition durations for the new current combatant
                        conditions = current.get("conditions", [])
                        remaining = []
                        for cond in conditions:
                            if cond.get("duration_type") == "rounds" and cond.get("duration") is not None:
                                cond["duration"] -= 1
                                if cond["duration"] > 0:
                                    remaining.append(cond)
                                # duration <= 0: condition expires (dropped from list)
                            else:
                                # indefinite or concentration: keep until manually removed
                                remaining.append(cond)
                        current["conditions"] = remaining

                elif action == "previous_turn":
                    # Go back to previous turn
                    if initiative["combatants"]:
                        initiative["current_turn_index"] -= 1
                        if initiative["current_turn_index"] < 0:
                            initiative["current_turn_index"] = len(initiative["combatants"]) - 1
                            initiative["round"] = max(1, initiative["round"] - 1)

                elif action == "end_combat":
                    # End combat and clear initiative
                    initiative = {"active": False, "round": 1, "current_turn_index": 0, "combatants": []}

                elif action == "roll_all":
                    # Roll initiative for all combatants
                    for combatant in initiative["combatants"]:
                        if combatant["initiative"] is None:
                            roll = random.randint(1, 20)
                            dex_mod = combatant.get("dex_mod", 0)
                            combatant["initiative"] = roll + dex_mod
                            combatant["roll"] = roll
                    # Sort
                    initiative["combatants"] = sorted(
                        initiative["combatants"],
                        key=lambda x: (x["initiative"] or -999, x.get("dex_mod", 0), x["name"]),
                        reverse=True,
                    )
                    initiative["current_turn_index"] = 0

                elif action == "use_action":
                    # Mark action as used for a combatant
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id and "action_economy" in combatant:
                            combatant["action_economy"]["action"] = False
                            break

                elif action == "use_bonus_action":
                    # Mark bonus action as used for a combatant
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id and "action_economy" in combatant:
                            combatant["action_economy"]["bonus_action"] = False
                            break

                elif action == "use_reaction":
                    # Mark reaction as used for a combatant
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id and "action_economy" in combatant:
                            combatant["action_economy"]["reaction"] = False
                            break

                elif action == "use_movement":
                    # Deduct movement from a combatant
                    combatant_id = init_data.get("combatant_id")
                    amount = init_data.get("amount", 5)
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id and "action_economy" in combatant:
                            current = combatant["action_economy"]["movement"]
                            combatant["action_economy"]["movement"] = max(0, current - amount)
                            break

                elif action == "reset_action_economy":
                    # Reset action economy for a combatant (DM override)
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id and "action_economy" in combatant:
                            combatant["action_economy"]["action"] = True
                            combatant["action_economy"]["bonus_action"] = True
                            combatant["action_economy"]["reaction"] = True
                            combatant["action_economy"]["movement"] = combatant["action_economy"].get("max_movement", 30)
                            break

                elif action == "update_npc":
                    # Update NPC stats (HP, etc) - DM only
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id and combatant.get("type") == "npc":
                            if "current_hp" in init_data:
                                combatant["current_hp"] = max(0, init_data["current_hp"])
                            if "max_hp" in init_data:
                                combatant["max_hp"] = init_data["max_hp"]
                            if "armor_class" in init_data:
                                combatant["armor_class"] = init_data["armor_class"]
                            break

                elif action == "add_condition":
                    # Add a condition to a combatant
                    combatant_id = init_data.get("combatant_id")
                    condition = {
                        "name": init_data.get("name", "Unknown"),
                        "duration": init_data.get("duration"),  # None = indefinite
                        "duration_type": init_data.get("duration_type", "indefinite"),
                        "source": init_data.get("source", ""),
                    }
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id:
                            conditions = combatant.get("conditions", [])
                            # Don't add duplicate conditions
                            if not any(c["name"] == condition["name"] for c in conditions):
                                conditions.append(condition)
                                combatant["conditions"] = conditions
                            break

                elif action == "remove_condition":
                    # Remove a condition from a combatant
                    combatant_id = init_data.get("combatant_id")
                    condition_name = init_data.get("name")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id:
                            conditions = combatant.get("conditions", [])
                            combatant["conditions"] = [c for c in conditions if c["name"] != condition_name]
                            break

                elif action == "clear_conditions":
                    # Remove all conditions from a combatant
                    combatant_id = init_data.get("combatant_id")
                    for combatant in initiative["combatants"]:
                        if combatant["id"] == combatant_id:
                            combatant["conditions"] = []
                            break

                else:
                    await manager.send_personal_message(
                        {"type": "error", "message": f"Unknown initiative action: {action}"},
                        websocket,
                    )
                    continue

                # Save to database (flag_modified ensures SQLAlchemy detects JSON changes)
                settings["initiative"] = initiative
                campaign.settings = settings
                flag_modified(campaign, "settings")
                db.commit()

                # Broadcast updated state to all clients
                await manager.broadcast_to_campaign(campaign_id, {"type": "initiative_state", "data": initiative})

            elif message_type == "map_update":
                # Broadcast map changes (token moves, additions, removals, fog, activation)
                # DM sends the update, all players receive it
                if not user.is_dm:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Only the DM can update the map"},
                        websocket,
                    )
                    continue

                map_data = data.get("data", {})
                await manager.broadcast_to_campaign(
                    campaign_id,
                    {"type": "map_update", "data": map_data},
                    exclude=websocket,
                )

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
