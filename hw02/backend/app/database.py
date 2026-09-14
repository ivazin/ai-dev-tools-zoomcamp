import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas import (
    EventData,
    Participant,
    Expense,
    Settlement,
    ActivityLog,
    SplitAllocation,
    LineItem,
    CurrencyCode,
    ActivityAction,
    CreateEventInput,
    CreateExpenseInput,
    UpdateExpenseInput,
    CreateSettlementInput,
    SplitType
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


AVATAR_COLORS = ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4", "#ef4444"]

# Reference rates relative to EUR (sample reference table)
RATES_TO_EUR: Dict[str, float] = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.18,
    "JPY": 0.0062,
    "CAD": 0.68,
    "CHF": 1.05,
    "AUD": 0.61,
}


def get_conversion_rate(from_curr: str, to_curr: str) -> float:
    if from_curr == to_curr:
        return 1.0
    from_eur = RATES_TO_EUR.get(from_curr, 1.0)
    to_eur = RATES_TO_EUR.get(to_curr, 1.0)
    # 1 from_curr = (from_eur / to_eur) to_curr
    return round(from_eur / to_eur, 6)


class MockDatabase:
    def __init__(self):
        self.events: Dict[str, EventData] = {}

    def reset(self):
        self.events.clear()

    def create_event(self, input_data: CreateEventInput) -> EventData:
        event_id = str(uuid.uuid4())[:12]
        created_at = now_iso()
        participants: List[Participant] = []

        # Creator
        creator_id = f"p-{uuid.uuid4().hex[:8]}"
        participants.append(
            Participant(
                id=creator_id,
                eventId=event_id,
                name=input_data.creatorName,
                avatarColor=AVATAR_COLORS[0],
                createdAt=created_at,
            )
        )

        # Initial participants
        for i, name in enumerate(input_data.initialParticipants):
            color = AVATAR_COLORS[(i + 1) % len(AVATAR_COLORS)]
            participants.append(
                Participant(
                    id=f"p-{uuid.uuid4().hex[:8]}",
                    eventId=event_id,
                    name=name,
                    avatarColor=color,
                    createdAt=created_at,
                )
            )

        activity_logs = [
            ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                eventId=event_id,
                actorId=creator_id,
                action=ActivityAction.EVENT_CREATED,
                details={"title": input_data.title, "baseCurrency": input_data.baseCurrency.value},
                createdAt=created_at,
            )
        ]

        event = EventData(
            id=event_id,
            title=input_data.title,
            baseCurrency=input_data.baseCurrency,
            createdAt=created_at,
            participants=participants,
            expenses=[],
            settlements=[],
            activityLogs=activity_logs,
        )
        self.events[event_id] = event
        return event

    def get_event(self, event_id: str) -> Optional[EventData]:
        return self.events.get(event_id)

    def add_participant(self, event_id: str, name: str) -> Optional[Participant]:
        event = self.get_event(event_id)
        if not event:
            return None

        # Check existing
        existing = next((p for p in event.participants if p.name.lower() == name.lower()), None)
        if existing:
            return existing

        created_at = now_iso()
        new_id = f"p-{uuid.uuid4().hex[:8]}"
        color = AVATAR_COLORS[len(event.participants) % len(AVATAR_COLORS)]
        participant = Participant(
            id=new_id,
            eventId=event_id,
            name=name,
            avatarColor=color,
            createdAt=created_at,
        )
        event.participants.append(participant)

        # Audit log
        event.activityLogs.append(
            ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                eventId=event_id,
                actorId=new_id,
                action=ActivityAction.PARTICIPANT_ADDED,
                details={"participantName": name, "participantId": new_id},
                createdAt=created_at,
            )
        )
        return participant

    def create_expense(self, event_id: str, input_data: CreateExpenseInput) -> Optional[Expense]:
        event = self.get_event(event_id)
        if not event:
            return None

        rate = get_conversion_rate(input_data.originalCurrency.value, event.baseCurrency.value)
        base_amount = round(input_data.originalAmount * rate, 2)
        created_at = now_iso()
        expense_id = f"exp-{uuid.uuid4().hex[:8]}"

        # Calculate splits
        splits: List[SplitAllocation] = []
        if input_data.isItemized and input_data.lineItems:
            # Itemized computation
            subtotal = sum(item.amount for item in input_data.lineItems)
            tax = input_data.taxAmount or 0.0
            tip = input_data.tipAmount or 0.0
            participant_shares: Dict[str, float] = {}

            for item in input_data.lineItems:
                if item.consumerIds:
                    share = item.amount / len(item.consumerIds)
                    for cid in item.consumerIds:
                        participant_shares[cid] = participant_shares.get(cid, 0.0) + share

            for cid, raw_share in participant_shares.items():
                ratio = (raw_share / subtotal) if subtotal > 0 else 0
                itemized_orig = raw_share + (tax + tip) * ratio
                comp_base = round(itemized_orig * rate, 2)
                splits.append(
                    SplitAllocation(
                        participantId=cid,
                        amount=round(itemized_orig, 2),
                        computedBaseAmount=comp_base,
                    )
                )
        else:
            # Total-amount split computation
            raw_splits = input_data.splits or []
            if not raw_splits:
                # Default equal to all participants
                raw_splits = [type("SplitTmp", (), {"participantId": p.id, "amount": None, "percentage": None, "shares": None}) for p in event.participants]

            split_type = input_data.splitType or SplitType.EQUAL
            if split_type == SplitType.EQUAL:
                equal_base = round(base_amount / len(raw_splits), 2) if raw_splits else 0.0
                for s in raw_splits:
                    splits.append(
                        SplitAllocation(
                            participantId=s.participantId,
                            computedBaseAmount=equal_base,
                        )
                    )
            elif split_type == SplitType.EXACT:
                for s in raw_splits:
                    amt = s.amount or 0.0
                    splits.append(
                        SplitAllocation(
                            participantId=s.participantId,
                            amount=amt,
                            computedBaseAmount=round(amt * rate, 2),
                        )
                    )
            elif split_type == SplitType.PERCENTAGE:
                for s in raw_splits:
                    pct = s.percentage or 0.0
                    splits.append(
                        SplitAllocation(
                            participantId=s.participantId,
                            percentage=pct,
                            computedBaseAmount=round(base_amount * (pct / 100.0), 2),
                        )
                    )
            elif split_type == SplitType.SHARES:
                total_shares = sum(s.shares or 1.0 for s in raw_splits) or 1.0
                for s in raw_splits:
                    sh = s.shares or 1.0
                    splits.append(
                        SplitAllocation(
                            participantId=s.participantId,
                            shares=sh,
                            computedBaseAmount=round(base_amount * (sh / total_shares), 2),
                        )
                    )

        line_items_data: Optional[List[LineItem]] = None
        if input_data.lineItems:
            line_items_data = [
                LineItem(
                    id=f"li-{uuid.uuid4().hex[:8]}",
                    title=item.title,
                    amount=item.amount,
                    consumerIds=item.consumerIds,
                )
                for item in input_data.lineItems
            ]

        expense = Expense(
            id=expense_id,
            eventId=event_id,
            payerId=input_data.payerId,
            description=input_data.description,
            originalAmount=input_data.originalAmount,
            originalCurrency=input_data.originalCurrency,
            exchangeRate=rate,
            baseAmount=base_amount,
            isItemized=input_data.isItemized,
            date=input_data.date or created_at,
            createdAt=created_at,
            updatedAt=created_at,
            splits=splits,
            lineItems=line_items_data,
            taxAmount=input_data.taxAmount,
            tipAmount=input_data.tipAmount,
        )

        event.expenses.append(expense)
        event.activityLogs.append(
            ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                eventId=event_id,
                actorId=input_data.payerId,
                action=ActivityAction.EXPENSE_CREATED,
                details={
                    "expenseId": expense_id,
                    "description": expense.description,
                    "baseAmount": expense.baseAmount,
                    "payerId": expense.payerId,
                },
                createdAt=created_at,
            )
        )
        return expense

    def update_expense(self, expense_id: str, input_data: UpdateExpenseInput) -> Optional[Expense]:
        for event in self.events.values():
            for i, exp in enumerate(event.expenses):
                if exp.id == expense_id:
                    updated_at = now_iso()
                    rate = exp.exchangeRate
                    orig_curr = input_data.originalCurrency or exp.originalCurrency
                    if orig_curr != exp.originalCurrency:
                        rate = get_conversion_rate(orig_curr.value, event.baseCurrency.value)

                    orig_amt = input_data.originalAmount if input_data.originalAmount is not None else exp.originalAmount
                    base_amt = round(orig_amt * rate, 2)

                    # Simple split recomputation if provided
                    splits = exp.splits
                    if input_data.splits:
                        equal_base = round(base_amt / len(input_data.splits), 2)
                        splits = [
                            SplitAllocation(
                                participantId=s.participantId,
                                computedBaseAmount=equal_base,
                            )
                            for s in input_data.splits
                        ]

                    updated_exp = Expense(
                        id=exp.id,
                        eventId=exp.eventId,
                        payerId=input_data.payerId or exp.payerId,
                        description=input_data.description or exp.description,
                        originalAmount=orig_amt,
                        originalCurrency=orig_curr,
                        exchangeRate=rate,
                        baseAmount=base_amt,
                        isItemized=input_data.isItemized if input_data.isItemized is not None else exp.isItemized,
                        date=input_data.date or exp.date,
                        createdAt=exp.createdAt,
                        updatedAt=updated_at,
                        splits=splits,
                        lineItems=exp.lineItems,
                        taxAmount=input_data.taxAmount if input_data.taxAmount is not None else exp.taxAmount,
                        tipAmount=input_data.tipAmount if input_data.tipAmount is not None else exp.tipAmount,
                    )
                    event.expenses[i] = updated_exp
                    event.activityLogs.append(
                        ActivityLog(
                            id=f"act-{uuid.uuid4().hex[:8]}",
                            eventId=event.id,
                            actorId=updated_exp.payerId,
                            action=ActivityAction.EXPENSE_UPDATED,
                            details={
                                "expenseId": expense_id,
                                "description": updated_exp.description,
                                "baseAmount": updated_exp.baseAmount,
                            },
                            createdAt=updated_at,
                        )
                    )
                    return updated_exp
        return None

    def delete_expense(self, event_id: str, expense_id: str, actor_id: str) -> bool:
        event = self.get_event(event_id)
        if not event:
            return False

        found_idx = next((i for i, exp in enumerate(event.expenses) if exp.id == expense_id), None)
        if found_idx is None:
            return False

        removed = event.expenses.pop(found_idx)
        created_at = now_iso()
        event.activityLogs.append(
            ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                eventId=event_id,
                actorId=actor_id,
                action=ActivityAction.EXPENSE_DELETED,
                details={
                    "expenseId": expense_id,
                    "description": removed.description,
                },
                createdAt=created_at,
            )
        )
        return True

    def create_settlement(self, event_id: str, input_data: CreateSettlementInput) -> Optional[Settlement]:
        event = self.get_event(event_id)
        if not event:
            return None

        created_at = now_iso()
        set_id = f"set-{uuid.uuid4().hex[:8]}"
        curr = input_data.currency or event.baseCurrency

        settlement = Settlement(
            id=set_id,
            eventId=event_id,
            fromParticipantId=input_data.fromParticipantId,
            toParticipantId=input_data.toParticipantId,
            amount=input_data.amount,
            currency=curr,
            date=input_data.date or created_at,
            createdAt=created_at,
        )
        event.settlements.append(settlement)
        event.activityLogs.append(
            ActivityLog(
                id=f"act-{uuid.uuid4().hex[:8]}",
                eventId=event_id,
                actorId=input_data.fromParticipantId,
                action=ActivityAction.SETTLEMENT_RECORDED,
                details={
                    "settlementId": set_id,
                    "fromParticipantId": input_data.fromParticipantId,
                    "toParticipantId": input_data.toParticipantId,
                    "amount": input_data.amount,
                },
                createdAt=created_at,
            )
        )
        return settlement


mock_db = MockDatabase()
