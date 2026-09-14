from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas import (
    EventData,
    CreateEventInput,
    Participant,
    AddParticipantInput,
    ErrorResponse,
)
from app.database import SqliteDatabase, get_db, now_iso
from app.services.broadcaster import broadcaster

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post(
    "",
    response_model=EventData,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_event(input_data: CreateEventInput, db: SqliteDatabase = Depends(get_db)):
    event = db.create_event(input_data)
    return event


@router.get(
    "/{eventId}",
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


@router.post(
    "/{eventId}/participants",
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
    await broadcaster.broadcast(
        eventId,
        {
            "type": "PARTICIPANT_ADDED",
            "actorId": participant.id,
            "timestamp": now_iso(),
            "payload": participant.model_dump(),
        },
    )
    return participant
