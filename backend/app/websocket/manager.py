from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""

    def __init__(self):
        # Store active connections by campaign_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, campaign_id: int, user_id: int, username: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        # Initialize campaign connections if not exists
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = set()

        # Add connection
        self.active_connections[campaign_id].add(websocket)
        self.connection_info[websocket] = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "username": username,
        }

        logger.info(f"User {username} (ID: {user_id}) connected to campaign {campaign_id}")

        # Notify others that a user connected
        await self.broadcast_to_campaign(
            campaign_id,
            {
                "type": "user_connected",
                "username": username,
                "user_id": user_id,
            },
            exclude=websocket,
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket not in self.connection_info:
            return

        info = self.connection_info[websocket]
        campaign_id = info["campaign_id"]
        username = info["username"]
        user_id = info["user_id"]

        # Remove from active connections
        if campaign_id in self.active_connections:
            self.active_connections[campaign_id].discard(websocket)
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]

        # Remove connection info
        del self.connection_info[websocket]

        logger.info(f"User {username} (ID: {user_id}) disconnected from campaign {campaign_id}")

        # Note: We can't await here since disconnect is not async
        # The broadcast will be handled by the WebSocket endpoint

    async def broadcast_to_campaign(self, campaign_id: int, message: dict, exclude: WebSocket = None):
        """Broadcast a message to all connections in a campaign."""
        if campaign_id not in self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected = []

        for connection in self.active_connections[campaign_id]:
            if connection == exclude:
                continue

            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    def get_campaign_connections(self, campaign_id: int) -> int:
        """Get the number of active connections for a campaign."""
        return len(self.active_connections.get(campaign_id, set()))


# Global connection manager instance
manager = ConnectionManager()
