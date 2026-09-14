from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional

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
from app.database import mock_db, get_conversion_rate

app = FastAPI(
    title="SplitWave Backend API",
    description="Backend REST API for SplitWave Collaborative Expense Splitter",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)},
    )


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
async def create_event(input_data: CreateEventInput):
    event = mock_db.create_event(input_data)
    return event


@app.get(
    "/api/events/{eventId}",
    response_model=EventData,
    responses={404: {"model": ErrorResponse}},
)
async def get_event(eventId: str):
    event = mock_db.get_event(eventId)
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
async def add_participant(eventId: str, body: AddParticipantInput):
    participant = mock_db.add_participant(eventId, body.name)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
        )
    return participant


# --- Expenses ---

@app.post(
    "/api/events/{eventId}/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def create_expense(eventId: str, input_data: CreateExpenseInput):
    expense = mock_db.create_expense(eventId, input_data)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
        )
    return expense


@app.put(
    "/api/expenses/{expenseId}",
    response_model=Expense,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_expense(expenseId: str, input_data: UpdateExpenseInput):
    updated = mock_db.update_expense(expenseId, input_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Expense with id "{expenseId}" not found.',
        )
    return updated


@app.delete(
    "/api/events/{eventId}/expenses/{expenseId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_expense(eventId: str, expenseId: str, body: DeleteExpenseInput):
    success = mock_db.delete_expense(eventId, expenseId, body.actorId)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event "{eventId}" or expense "{expenseId}" not found.',
        )
    return None


# --- Settlements ---

@app.post(
    "/api/events/{eventId}/settlements",
    response_model=Settlement,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def create_settlement(eventId: str, input_data: CreateSettlementInput):
    settlement = mock_db.create_settlement(eventId, input_data)
    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Event with id "{eventId}" not found.',
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
