from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class CurrencyCode(str, Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    CHF = "CHF"
    AUD = "AUD"


class SplitType(str, Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"
    SHARES = "SHARES"


class ActivityAction(str, Enum):
    EVENT_CREATED = "EVENT_CREATED"
    PARTICIPANT_ADDED = "PARTICIPANT_ADDED"
    EXPENSE_CREATED = "EXPENSE_CREATED"
    EXPENSE_UPDATED = "EXPENSE_UPDATED"
    EXPENSE_DELETED = "EXPENSE_DELETED"
    SETTLEMENT_RECORDED = "SETTLEMENT_RECORDED"


class Participant(BaseModel):
    id: str
    eventId: str
    name: str
    avatarColor: str
    createdAt: str


class AddParticipantInput(BaseModel):
    name: str


class SplitAllocation(BaseModel):
    participantId: str
    amount: Optional[float] = None
    percentage: Optional[float] = None
    shares: Optional[float] = None
    computedBaseAmount: float


class LineItem(BaseModel):
    id: str
    title: str
    amount: float
    consumerIds: List[str]


class Expense(BaseModel):
    id: str
    eventId: str
    payerId: str
    description: str
    originalAmount: float
    originalCurrency: CurrencyCode
    exchangeRate: float
    baseAmount: float
    isItemized: bool
    category: Optional[str] = None
    date: str
    createdAt: str
    updatedAt: str
    splits: List[SplitAllocation]
    lineItems: Optional[List[LineItem]] = None
    taxAmount: Optional[float] = None
    tipAmount: Optional[float] = None


class Settlement(BaseModel):
    id: str
    eventId: str
    fromParticipantId: str
    toParticipantId: str
    amount: float
    currency: CurrencyCode
    date: str
    createdAt: str


class ActivityLog(BaseModel):
    id: str
    eventId: str
    actorId: str
    action: ActivityAction
    details: Dict[str, Any] = Field(default_factory=dict)
    createdAt: str


class EventData(BaseModel):
    id: str
    title: str
    baseCurrency: CurrencyCode
    createdAt: str
    participants: List[Participant]
    expenses: List[Expense]
    settlements: List[Settlement]
    activityLogs: List[ActivityLog]


class CreateEventInput(BaseModel):
    title: str
    baseCurrency: CurrencyCode
    creatorName: str
    initialParticipants: List[str]


class SplitInput(BaseModel):
    participantId: str
    amount: Optional[float] = None
    percentage: Optional[float] = None
    shares: Optional[float] = None


class LineItemInput(BaseModel):
    title: str
    amount: float
    consumerIds: List[str]


class CreateExpenseInput(BaseModel):
    eventId: str
    payerId: str
    description: str
    originalAmount: float
    originalCurrency: CurrencyCode
    date: Optional[str] = None
    isItemized: bool
    splits: Optional[List[SplitInput]] = None
    splitType: Optional[SplitType] = None
    lineItems: Optional[List[LineItemInput]] = None
    taxAmount: Optional[float] = None
    tipAmount: Optional[float] = None


class UpdateExpenseInput(BaseModel):
    eventId: Optional[str] = None
    payerId: Optional[str] = None
    description: Optional[str] = None
    originalAmount: Optional[float] = None
    originalCurrency: Optional[CurrencyCode] = None
    date: Optional[str] = None
    isItemized: Optional[bool] = None
    splits: Optional[List[SplitInput]] = None
    splitType: Optional[SplitType] = None
    lineItems: Optional[List[LineItemInput]] = None
    taxAmount: Optional[float] = None
    tipAmount: Optional[float] = None


class DeleteExpenseInput(BaseModel):
    actorId: str


class CreateSettlementInput(BaseModel):
    eventId: str
    fromParticipantId: str
    toParticipantId: str
    amount: float
    currency: Optional[CurrencyCode] = None
    date: Optional[str] = None


class ExchangeRateResponse(BaseModel):
    rate: float
    date: str


class ErrorResponse(BaseModel):
    message: str
