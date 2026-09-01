"""
WebSocket routes for authenticated real-time queue updates and targeted farmer notifications.
Hardened with JWT Token verification.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.core.security import decode_token
from app.core.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/queue/{centre_id}")
async def queue_websocket(websocket: WebSocket, centre_id: int):
    """
    Connect to receive real-time queue events for a specific procurement centre.
    """
    await manager.connect_to_centre(websocket, centre_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_from_centre(websocket, centre_id)


@router.websocket("/ws/user/{user_id}")
async def user_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str | None = Query(default=None),
):
    """
    Connect for private, targeted user notifications (e.g., FARMER_CALLED event).
    Strictly verifies JWT authentication so users cannot eavesdrop on other users.
    """
    if token:
        try:
            payload = decode_token(token)
            auth_user_id = int(payload.get("sub", "-1"))
            if auth_user_id != user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect_user(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(user_id)
