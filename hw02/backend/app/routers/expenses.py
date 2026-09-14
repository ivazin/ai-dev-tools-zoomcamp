from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas import (
    Expense,
    CreateExpenseInput,
    UpdateExpenseInput,
    DeleteExpenseInput,
    ErrorResponse,
)
from app.database import SqliteDatabase, get_db, now_iso
from app.services.broadcaster import broadcaster

router = APIRouter(tags=["Expenses"])


@router.post(
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
    await broadcaster.broadcast(
        eventId,
        {
            "type": "EXPENSE_CREATED",
            "actorId": expense.payerId,
            "timestamp": now_iso(),
            "payload": expense.model_dump(),
        },
    )
    return expense


@router.put(
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
    await broadcaster.broadcast(
        updated.eventId,
        {
            "type": "EXPENSE_UPDATED",
            "actorId": updated.payerId,
            "timestamp": now_iso(),
            "payload": updated.model_dump(),
        },
    )
    return updated


@router.delete(
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
    await broadcaster.broadcast(
        eventId,
        {
            "type": "EXPENSE_DELETED",
            "actorId": body.actorId,
            "timestamp": now_iso(),
            "payload": {"expenseId": expenseId},
        },
    )
    return None
