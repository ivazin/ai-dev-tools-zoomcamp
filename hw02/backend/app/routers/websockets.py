import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

from app.services.broadcaster import broadcaster

router = APIRouter(tags=["WebSockets"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.websocket("/ws/events/{eventId}")
async def websocket_endpoint(websocket: WebSocket, eventId: str):
    await broadcaster.connect(websocket, eventId)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                msg_type = data.get("type")
                if msg_type == "JOIN":
                    participant_id = data.get("participantId")
                    if participant_id:
                        broadcaster.register_participant(websocket, eventId, participant_id)
                        # Broadcast updated presence
                        await broadcaster.broadcast(
                            eventId,
                            {
                                "type": "PRESENCE_CHANGE",
                                "timestamp": now_iso(),
                                "payload": {"onlineParticipants": list(broadcaster.online_users.get(eventId, set()))},
                            },
                        )
            except Exception:
                pass
    except WebSocketDisconnect:
        await broadcaster.disconnect(websocket)
