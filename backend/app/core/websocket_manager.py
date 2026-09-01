"""
WebSocket connection manager for real-time queue broadcasting.
Manages connections grouped by procurement centre ID.
"""
import json
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """
    Maintains active WebSocket connections.
    Clients subscribe to a specific centre's queue channel.
    """

    def __init__(self):
        # centre_id -> list of connected websockets
        self.centre_connections: Dict[int, List[WebSocket]] = defaultdict(list)
        # user_id -> websocket (for targeted farmer notifications)
        self.user_connections: Dict[int, WebSocket] = {}

    async def connect_to_centre(self, websocket: WebSocket, centre_id: int):
        await websocket.accept()
        self.centre_connections[centre_id].append(websocket)

    async def connect_user(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.user_connections[user_id] = websocket

    def disconnect_from_centre(self, websocket: WebSocket, centre_id: int):
        connections = self.centre_connections.get(centre_id, [])
        if websocket in connections:
            connections.remove(websocket)

    def disconnect_user(self, user_id: int):
        self.user_connections.pop(user_id, None)

    async def broadcast_to_centre(self, centre_id: int, event: str, data: dict):
        """Send a real-time event to ALL connections watching a centre's queue."""
        payload = json.dumps({"event": event, "data": data})
        dead = []
        for ws in self.centre_connections.get(centre_id, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.centre_connections[centre_id].remove(ws)

    async def send_to_user(self, user_id: int, event: str, data: dict):
        """Send a targeted notification to a specific farmer."""
        ws = self.user_connections.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps({"event": event, "data": data}))
            except Exception:
                self.disconnect_user(user_id)


# Singleton instance — imported throughout the app
manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Queue Event Constants
# ---------------------------------------------------------------------------
class QueueEvent:
    QUEUE_UPDATED = "QUEUE_UPDATED"
    FARMER_CALLED = "FARMER_CALLED"
    QUEUE_DELAYED = "QUEUE_DELAYED"
    PROCUREMENT_STARTED = "PROCUREMENT_STARTED"
    PROCUREMENT_COMPLETED = "PROCUREMENT_COMPLETED"
    PAYMENT_UPDATED = "PAYMENT_UPDATED"
    NOTIFICATION = "NOTIFICATION"
