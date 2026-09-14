from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query

from app.schemas import CurrencyCode, ExchangeRateResponse, ErrorResponse
from app.database import get_conversion_rate

router = APIRouter(prefix="/api/exchange-rates", tags=["Exchange Rates"])


@router.get(
    "",
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
