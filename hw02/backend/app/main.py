import json
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Optional, Dict, Set

from app.schemas import (
    EventData,
    Participant,
    AddParticipantInput,
    Expense,
    CreateEventInput,
    CreateExpenseInput,
    UpdateExpenseInput,
    DeleteExpenseInput,
    Settlement,
    CreateSettlementInput,
    ExchangeRateResponse,
    CurrencyCode,
    ErrorResponse,
)
from app.config import get_settings
from app.database import mock_db, get_db, SqliteDatabase, get_conversion_rate, now_iso

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend REST API for Tavli Collaborative Expense Splitter",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )


# --- WebSocket Real-Time Connection Manager ---

class ConnectionManager:
    def __init__(self):
        # event_id -> set of active WebSockets
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # socket -> (event_id, participant_id)
        self.socket_info: Dict[WebSocket, tuple[str, str]] = {}
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

            await self.broadcast(
                event_id,
                {
                    "type": "PRESENCE_CHANGE",
                    "timestamp": now_iso(),
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


manager = ConnectionManager()


@app.websocket("/ws/events/{eventId}")
async def websocket_endpoint(websocket: WebSocket, eventId: str):
    await manager.connect(websocket, eventId)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                msg_type = data.get("type")
                if msg_type == "JOIN":
                    participant_id = data.get("participantId")
                    if participant_id:
                        manager.register_participant(websocket, eventId, participant_id)
                        # Broadcast updated presence
                        await manager.broadcast(
                            eventId,
                            {
                                "type": "PRESENCE_CHANGE",
                                "timestamp": now_iso(),
                                "payload": {"onlineParticipants": list(manager.online_users.get(eventId, set()))},
                            },
                        )
            except Exception:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


# --- Health Probes ---

@app.get("/api/health/live")
async def health_live():
    return {"status": "ok"}


@app.get("/api/health/ready")
async def health_ready():
    return {"status": "ready"}


# --- Events ---

@app.post(
    "/api/events",
    response_model=EventData,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_event(input_data: CreateEventInput, db: SqliteDatabase = Depends(get_db)):
    event = db.create_event(input_data)
    return event


@app.get(
    "/api/events/{eventId}",
    response_model=EventData,
    responses={404: {"model": ErrorResponse}},
)
async def get_event(eventId: str, db: SqliteDatabase = Depends(get_db)):
    event = db.get_event(eventId)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
        )
    return event


@app.post(
    "/api/events/{eventId}/participants",
    response_model=Participant,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
async def add_participant(eventId: str, body: AddParticipantInput, db: SqliteDatabase = Depends(get_db)):
    participant = db.add_participant(eventId, body.name)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
        )
    await manager.broadcast(
        eventId,
        {
            "type": "PARTICIPANT_ADDED",
            "actorId": participant.id,
            "timestamp": now_iso(),
            "payload": participant.model_dump(),
        },
    )
    return participant


# --- Expenses ---

@app.post(
    "/api/events/{eventId}/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def create_expense(eventId: str, input_data: CreateExpenseInput, db: SqliteDatabase = Depends(get_db)):
    expense = db.create_expense(eventId, input_data)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
        )
    await manager.broadcast(
        eventId,
        {
            "type": "EXPENSE_CREATED",
            "actorId": expense.payerId,
            "timestamp": now_iso(),
            "payload": expense.model_dump(),
        },
    )
    return expense


@app.put(
    "/api/expenses/{expenseId}",
    response_model=Expense,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_expense(expenseId: str, input_data: UpdateExpenseInput, db: SqliteDatabase = Depends(get_db)):
    updated = db.update_expense(expenseId, input_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Expense with id "{expenseId}" not found.',
        )
    await manager.broadcast(
        updated.eventId,
        {
            "type": "EXPENSE_UPDATED",
            "actorId": updated.payerId,
            "timestamp": now_iso(),
            "payload": updated.model_dump(),
        },
    )
    return updated


@app.delete(
    "/api/events/{eventId}/expenses/{expenseId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_expense(eventId: str, expenseId: str, body: DeleteExpenseInput, db: SqliteDatabase = Depends(get_db)):
    success = db.delete_expense(eventId, expenseId, body.actorId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event "{eventId}" or expense "{expenseId}" not found.',
        )
    await manager.broadcast(
        eventId,
        {
            "type": "EXPENSE_DELETED",
            "actorId": body.actorId,
            "timestamp": now_iso(),
            "payload": {"expenseId": expenseId},
        },
    )
    return None


# --- Settlements ---

@app.post(
    "/api/events/{eventId}/settlements",
    response_model=Settlement,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def create_settlement(eventId: str, input_data: CreateSettlementInput, db: SqliteDatabase = Depends(get_db)):
    settlement = db.create_settlement(eventId, input_data)
    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
        )
    await manager.broadcast(
        eventId,
        {
            "type": "SETTLEMENT_RECORDED",
            "actorId": settlement.fromParticipantId,
            "timestamp": now_iso(),
            "payload": settlement.model_dump(),
        },
    )
    return settlement


# --- Exchange Rates ---

@app.get(
    "/api/exchange-rates",
    response_model=ExchangeRateResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_exchange_rate(
    from_curr: CurrencyCode = Query(..., alias="from"),
    to_curr: CurrencyCode = Query(..., alias="to"),
    date: Optional[str] = Query(None),
):
    rate = get_conversion_rate(from_curr.value, to_curr.value)
    effective_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return ExchangeRateResponse(rate=rate, date=effective_date)
