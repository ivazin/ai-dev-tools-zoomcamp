import json
from typing import Dict, Set, Tuple
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections, rooms per event, and presence state.
    """
    def __init__(self):
        # event_id -> set of active WebSockets
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # socket -> (event_id, participant_id)
        self.socket_info: Dict[WebSocket, Tuple[str, str]] = {}
        # event_id -> set of online participant IDs
        self.online_users: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, event_id: str):
        await websocket.accept()
        if event_id not in self.rooms:
            self.rooms[event_id] = set()
            self.online_users[event_id] = set()
        self.rooms[event_id].add(websocket)

    def register_participant(self, websocket: WebSocket, event_id: str, participant_id: str):
        self.socket_info[websocket] = (event_id, participant_id)
        if event_id not in self.online_users:
            self.online_users[event_id] = set()
        self.online_users[event_id].add(participant_id)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.socket_info:
            event_id, participant_id = self.socket_info.pop(websocket)
            if event_id in self.rooms:
                self.rooms[event_id].discard(websocket)

            # Check if participant has other active sockets in this room
            has_other = any(
                p_id == participant_id and e_id == event_id
                for e_id, p_id in self.socket_info.values()
            )
            if not has_other and event_id in self.online_users:
                self.online_users[event_id].discard(participant_id)

            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            await self.broadcast(
                event_id,
                {
                    "type": "PRESENCE_CHANGE",
                    "timestamp": now_iso,
                    "payload": {"onlineParticipants": list(self.online_users.get(event_id, set()))},
                },
            )
        else:
            # Sockets that never sent JOIN
            for event_id, sockets in list(self.rooms.items()):
                sockets.discard(websocket)

    async def broadcast(self, event_id: str, message: dict):
        if event_id not in self.rooms:
            return
        dead_sockets = set()
        msg_str = json.dumps(message)
        for ws in self.rooms[event_id]:
            try:
                await ws.send_text(msg_str)
            except Exception:
                dead_sockets.add(ws)

        for ws in dead_sockets:
            await self.disconnect(ws)


broadcaster = ConnectionManager()
