from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas import (
    Settlement,
    CreateSettlementInput,
    ErrorResponse,
)
from app.database import SqliteDatabase, get_db, now_iso
from app.services.broadcaster import broadcaster

router = APIRouter(prefix="/api/events/{eventId}/settlements", tags=["Settlements"])


@router.post(
    "",
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
    await broadcaster.broadcast(
        eventId,
        {
            "type": "SETTLEMENT_RECORDED",
            "actorId": settlement.fromParticipantId,
            "timestamp": now_iso(),
            "payload": settlement.model_dump(),
        },
    )
    return settlement
