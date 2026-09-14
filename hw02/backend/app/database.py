import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session, joinedload

from app.config import get_settings
from app.models import (
    Base,
    EventModel,
    ParticipantModel,
    ExpenseModel,
    ExpenseSplitModel,
    LineItemModel,
    SettlementModel,
    ActivityLogModel,
)
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
    SplitType,
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
    return round(from_eur / to_eur, 6)


class SqliteDatabase:
    """
    SQLAlchemy-backed persistence service implementing the database contract.
    Named SqliteDatabase for full backwards-compatibility with existing tests and imports.
    """

    def __init__(self, db_path: Optional[Path | str] = None, database_url: Optional[str] = None):
        if database_url:
            self.database_url = database_url
        elif db_path:
            self.database_url = f"sqlite:///{db_path}"
        else:
            self.database_url = get_settings().DATABASE_URL

        connect_args = {}
        if self.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self.engine = create_engine(self.database_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        self._init_db()
        self._seed_sample_event_if_empty()

    def _init_db(self):
        Base.metadata.create_all(bind=self.engine)

    def _seed_sample_event_if_empty(self):
        with self.SessionLocal() as session:
            existing = session.query(EventModel).filter(EventModel.id == "barcelona-trip-2026").first()
            if existing:
                return

            created_at = "2026-09-12T10:00:00.000Z"
            event = EventModel(
                id="barcelona-trip-2026",
                title="Barcelona Getaway",
                base_currency="EUR",
                created_at=created_at,
            )
            session.add(event)

            participants = [
                ParticipantModel(id="p-max", event_id="barcelona-trip-2026", name="Max", avatar_color="#3B82F6", created_at=created_at),
                ParticipantModel(id="p-sarah", event_id="barcelona-trip-2026", name="Sarah", avatar_color="#10B981", created_at=created_at),
                ParticipantModel(id="p-alex", event_id="barcelona-trip-2026", name="Alex", avatar_color="#F59E0B", created_at=created_at),
                ParticipantModel(id="p-elena", event_id="barcelona-trip-2026", name="Elena", avatar_color="#EC4899", created_at=created_at),
            ]
            session.add_all(participants)

            # Expense 1: AirBnb Sagrada Familia (480 EUR, Equal)
            exp1 = ExpenseModel(
                id="exp-1",
                event_id="barcelona-trip-2026",
                payer_id="p-max",
                description="AirBnb Sagrada Familia",
                original_amount=480.0,
                original_currency="EUR",
                exchange_rate=1.0,
                base_amount=480.0,
                is_itemized=False,
                date="2026-09-12T12:00:00.000Z",
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(exp1)
            for pid in ["p-max", "p-sarah", "p-alex", "p-elena"]:
                session.add(
                    ExpenseSplitModel(
                        id=f"sp-{uuid.uuid4().hex[:8]}",
                        expense_id="exp-1",
                        participant_id=pid,
                        computed_base_amount=120.0,
                    )
                )

            # Expense 2: Dinner at Can Culleretes (96 EUR, itemized)
            exp2 = ExpenseModel(
                id="exp-2",
                event_id="barcelona-trip-2026",
                payer_id="p-sarah",
                description="Dinner at Can Culleretes",
                original_amount=96.0,
                original_currency="EUR",
                exchange_rate=1.0,
                base_amount=96.0,
                is_itemized=True,
                tax_amount=8.0,
                tip_amount=10.0,
                date="2026-09-13T20:00:00.000Z",
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(exp2)
            session.add(
                LineItemModel(
                    id="li-1",
                    expense_id="exp-2",
                    title="Paella Valenciana (x2)",
                    amount=42.0,
                    consumer_ids_json=json.dumps(["p-max", "p-sarah", "p-alex"]),
                )
            )
            session.add(
                LineItemModel(
                    id="li-2",
                    expense_id="exp-2",
                    title="Tapas & Sangria",
                    amount=36.0,
                    consumer_ids_json=json.dumps(["p-max", "p-sarah", "p-elena"]),
                )
            )
            splits_data = [
                ("p-max", 32.0),
                ("p-sarah", 32.0),
                ("p-alex", 17.23),
                ("p-elena", 14.77),
            ]
            for pid, amt in splits_data:
                session.add(
                    ExpenseSplitModel(
                        id=f"sp-{uuid.uuid4().hex[:8]}",
                        expense_id="exp-2",
                        participant_id=pid,
                        computed_base_amount=amt,
                    )
                )

            # Expense 3: Duty-free Snacks (54.25 USD -> 50.0 EUR)
            exp3 = ExpenseModel(
                id="exp-3",
                event_id="barcelona-trip-2026",
                payer_id="p-alex",
                description="Duty-free Snacks & Drinks",
                original_amount=54.25,
                original_currency="USD",
                exchange_rate=0.921659,
                base_amount=50.0,
                is_itemized=False,
                date="2026-09-14T08:00:00.000Z",
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(exp3)
            for pid in ["p-alex", "p-elena"]:
                session.add(
                    ExpenseSplitModel(
                        id=f"sp-{uuid.uuid4().hex[:8]}",
                        expense_id="exp-3",
                        participant_id=pid,
                        computed_base_amount=25.0,
                    )
                )

            # Activity logs
            logs = [
                ActivityLogModel(
                    id="act-1",
                    event_id="barcelona-trip-2026",
                    actor_id="p-max",
                    action="EVENT_CREATED",
                    details_json=json.dumps({"title": "Barcelona Getaway", "baseCurrency": "EUR"}),
                    created_at=created_at,
                ),
                ActivityLogModel(
                    id="act-2",
                    event_id="barcelona-trip-2026",
                    actor_id="p-max",
                    action="EXPENSE_CREATED",
                    details_json=json.dumps({"description": "AirBnb Sagrada Familia", "amount": 480.0, "currency": "EUR"}),
                    created_at=created_at,
                ),
                ActivityLogModel(
                    id="act-3",
                    event_id="barcelona-trip-2026",
                    actor_id="p-sarah",
                    action="EXPENSE_CREATED",
                    details_json=json.dumps({"description": "Dinner at Can Culleretes", "amount": 96.0, "currency": "EUR", "itemized": True}),
                    created_at=created_at,
                ),
                ActivityLogModel(
                    id="act-4",
                    event_id="barcelona-trip-2026",
                    actor_id="p-alex",
                    action="EXPENSE_CREATED",
                    details_json=json.dumps({"description": "Duty-free Snacks & Drinks", "amount": 54.25, "currency": "USD", "baseAmount": 50.0}),
                    created_at=created_at,
                ),
            ]
            session.add_all(logs)
            session.commit()

    def reset(self):
        with self.SessionLocal() as session:
            for model in [
                ActivityLogModel,
                SettlementModel,
                LineItemModel,
                ExpenseSplitModel,
                ExpenseModel,
                ParticipantModel,
                EventModel,
            ]:
                session.query(model).delete()
            session.commit()

    def create_event(self, input_data: CreateEventInput) -> EventData:
        event_id = str(uuid.uuid4())[:12]
        created_at = now_iso()

        creator_id = f"p-{uuid.uuid4().hex[:8]}"
        participants: List[Participant] = [
            Participant(
                id=creator_id,
                eventId=event_id,
                name=input_data.creatorName,
                avatarColor=AVATAR_COLORS[0],
                createdAt=created_at,
            )
        ]

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

        with self.SessionLocal() as session:
            ev_model = EventModel(
                id=event_id,
                title=input_data.title,
                base_currency=input_data.baseCurrency.value,
                created_at=created_at,
            )
            session.add(ev_model)

            for p in participants:
                session.add(
                    ParticipantModel(
                        id=p.id,
                        event_id=p.eventId,
                        name=p.name,
                        avatar_color=p.avatarColor,
                        created_at=p.createdAt,
                    )
                )

            for log in activity_logs:
                session.add(
                    ActivityLogModel(
                        id=log.id,
                        event_id=log.eventId,
                        actor_id=log.actorId,
                        action=log.action.value,
                        details_json=json.dumps(log.details),
                        created_at=log.createdAt,
                    )
                )
            session.commit()

        return EventData(
            id=event_id,
            title=input_data.title,
            baseCurrency=input_data.baseCurrency,
            createdAt=created_at,
            participants=participants,
            expenses=[],
            settlements=[],
            activityLogs=activity_logs,
        )

    def get_event(self, event_id: str) -> Optional[EventData]:
        with self.SessionLocal() as session:
            ev = (
                session.query(EventModel)
                .options(
                    joinedload(EventModel.participants),
                    joinedload(EventModel.settlements),
                    joinedload(EventModel.activity_logs),
                )
                .filter(EventModel.id == event_id)
                .first()
            )
            if not ev:
                return None

            participants = [
                Participant(
                    id=p.id,
                    eventId=p.event_id,
                    name=p.name,
                    avatarColor=p.avatar_color,
                    createdAt=p.created_at,
                )
                for p in sorted(ev.participants, key=lambda x: x.created_at)
            ]

            # Fetch expenses with splits & line items
            exp_models = (
                session.query(ExpenseModel)
                .options(
                    joinedload(ExpenseModel.splits),
                    joinedload(ExpenseModel.line_items),
                )
                .filter(ExpenseModel.event_id == event_id)
                .order_by(ExpenseModel.date.desc(), ExpenseModel.created_at.desc())
                .all()
            )

            expenses: List[Expense] = []
            for em in exp_models:
                splits = [
                    SplitAllocation(
                        participantId=s.participant_id,
                        amount=s.amount,
                        percentage=s.percentage,
                        shares=s.shares,
                        computedBaseAmount=s.computed_base_amount,
                    )
                    for s in em.splits
                ]

                line_items = [
                    LineItem(
                        id=li.id,
                        title=li.title,
                        amount=li.amount,
                        consumerIds=json.loads(li.consumer_ids_json),
                    )
                    for li in em.line_items
                ] if em.line_items else None

                expenses.append(
                    Expense(
                        id=em.id,
                        eventId=em.event_id,
                        payerId=em.payer_id,
                        description=em.description,
                        originalAmount=em.original_amount,
                        originalCurrency=CurrencyCode(em.original_currency),
                        exchangeRate=em.exchange_rate,
                        baseAmount=em.base_amount,
                        isItemized=em.is_itemized,
                        category=em.category,
                        date=em.date,
                        createdAt=em.created_at,
                        updatedAt=em.updated_at,
                        splits=splits,
                        lineItems=line_items,
                        taxAmount=em.tax_amount,
                        tipAmount=em.tip_amount,
                    )
                )

            settlements = [
                Settlement(
                    id=s.id,
                    eventId=s.event_id,
                    fromParticipantId=s.from_participant_id,
                    toParticipantId=s.to_participant_id,
                    amount=s.amount,
                    currency=CurrencyCode(s.currency),
                    date=s.date,
                    createdAt=s.created_at,
                )
                for s in sorted(ev.settlements, key=lambda x: (x.date, x.created_at), reverse=True)
            ]

            activity_logs = [
                ActivityLog(
                    id=a.id,
                    eventId=a.event_id,
                    actorId=a.actor_id,
                    action=ActivityAction(a.action),
                    details=json.loads(a.details_json),
                    createdAt=a.created_at,
                )
                for a in sorted(ev.activity_logs, key=lambda x: x.created_at, reverse=True)
            ]

            return EventData(
                id=ev.id,
                title=ev.title,
                baseCurrency=CurrencyCode(ev.base_currency),
                createdAt=ev.created_at,
                participants=participants,
                expenses=expenses,
                settlements=settlements,
                activityLogs=activity_logs,
            )

    def add_participant(self, event_id: str, name: str) -> Optional[Participant]:
        event = self.get_event(event_id)
        if not event:
            return None

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

        act_id = f"act-{uuid.uuid4().hex[:8]}"
        act_details = json.dumps({"participantName": name, "participantId": new_id})

        with self.SessionLocal() as session:
            p_model = ParticipantModel(
                id=participant.id,
                event_id=participant.eventId,
                name=participant.name,
                avatar_color=participant.avatarColor,
                created_at=participant.createdAt,
            )
            session.add(p_model)

            act_model = ActivityLogModel(
                id=act_id,
                event_id=event_id,
                actor_id=new_id,
                action=ActivityAction.PARTICIPANT_ADDED.value,
                details_json=act_details,
                created_at=created_at,
            )
            session.add(act_model)
            session.commit()

        return participant

    def create_expense(self, event_id: str, input_data: CreateExpenseInput) -> Optional[Expense]:
        event = self.get_event(event_id)
        if not event:
            return None

        rate = get_conversion_rate(input_data.originalCurrency.value, event.baseCurrency.value)
        base_amount = round(input_data.originalAmount * rate, 2)
        created_at = now_iso()
        expense_id = f"exp-{uuid.uuid4().hex[:8]}"

        splits: List[SplitAllocation] = []
        if input_data.isItemized and input_data.lineItems:
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
            raw_splits = input_data.splits or []
            if not raw_splits:
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

        act_id = f"act-{uuid.uuid4().hex[:8]}"
        act_details = json.dumps({
            "expenseId": expense_id,
            "description": expense.description,
            "baseAmount": expense.baseAmount,
            "payerId": expense.payerId,
        })

        with self.SessionLocal() as session:
            exp_model = ExpenseModel(
                id=expense.id,
                event_id=expense.eventId,
                payer_id=expense.payerId,
                description=expense.description,
                original_amount=expense.originalAmount,
                original_currency=expense.originalCurrency.value,
                exchange_rate=expense.exchangeRate,
                base_amount=expense.baseAmount,
                is_itemized=expense.isItemized,
                date=expense.date,
                created_at=expense.createdAt,
                updated_at=expense.updatedAt,
                tax_amount=expense.taxAmount,
                tip_amount=expense.tipAmount,
            )
            session.add(exp_model)

            for s in splits:
                session.add(
                    ExpenseSplitModel(
                        id=f"sp-{uuid.uuid4().hex[:8]}",
                        expense_id=expense_id,
                        participant_id=s.participantId,
                        amount=s.amount,
                        percentage=s.percentage,
                        shares=s.shares,
                        computed_base_amount=s.computedBaseAmount,
                    )
                )

            if line_items_data:
                for li in line_items_data:
                    session.add(
                        LineItemModel(
                            id=li.id,
                            expense_id=expense_id,
                            title=li.title,
                            amount=li.amount,
                            consumer_ids_json=json.dumps(li.consumerIds),
                        )
                    )

            session.add(
                ActivityLogModel(
                    id=act_id,
                    event_id=event_id,
                    actor_id=input_data.payerId,
                    action=ActivityAction.EXPENSE_CREATED.value,
                    details_json=act_details,
                    created_at=created_at,
                )
            )
            session.commit()

        return expense

    def update_expense(self, expense_id: str, input_data: UpdateExpenseInput) -> Optional[Expense]:
        with self.SessionLocal() as session:
            exp = session.query(ExpenseModel).filter(ExpenseModel.id == expense_id).first()
            if not exp:
                return None

            event = session.query(EventModel).filter(EventModel.id == exp.event_id).first()
            if not event:
                return None

            base_currency = event.base_currency
            updated_at = now_iso()

            orig_curr = input_data.originalCurrency.value if input_data.originalCurrency else exp.original_currency
            rate = exp.exchange_rate
            if orig_curr != exp.original_currency:
                rate = get_conversion_rate(orig_curr, base_currency)

            orig_amt = input_data.originalAmount if input_data.originalAmount is not None else exp.original_amount
            base_amt = round(orig_amt * rate, 2)

            description = input_data.description if input_data.description is not None else exp.description
            payer_id = input_data.payerId or exp.payer_id
            is_itemized = input_data.isItemized if input_data.isItemized is not None else exp.is_itemized
            date = input_data.date or exp.date
            tax_amount = input_data.taxAmount if input_data.taxAmount is not None else exp.tax_amount
            tip_amount = input_data.tipAmount if input_data.tipAmount is not None else exp.tip_amount

            exp.payer_id = payer_id
            exp.description = description
            exp.original_amount = orig_amt
            exp.original_currency = orig_curr
            exp.exchange_rate = rate
            exp.base_amount = base_amt
            exp.is_itemized = is_itemized
            exp.date = date
            exp.updated_at = updated_at
            exp.tax_amount = tax_amount
            exp.tip_amount = tip_amount

            # Update splits if provided
            if input_data.splits:
                session.query(ExpenseSplitModel).filter(ExpenseSplitModel.expense_id == expense_id).delete()
                equal_base = round(base_amt / len(input_data.splits), 2)
                for s in input_data.splits:
                    session.add(
                        ExpenseSplitModel(
                            id=f"sp-{uuid.uuid4().hex[:8]}",
                            expense_id=expense_id,
                            participant_id=s.participantId,
                            computed_base_amount=equal_base,
                        )
                    )

            # Activity log
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            act_details = json.dumps({
                "expenseId": expense_id,
                "description": description,
                "baseAmount": base_amt,
            })
            session.add(
                ActivityLogModel(
                    id=act_id,
                    event_id=exp.event_id,
                    actor_id=payer_id,
                    action=ActivityAction.EXPENSE_UPDATED.value,
                    details_json=act_details,
                    created_at=updated_at,
                )
            )
            session.commit()

        # Re-fetch the updated expense
        with self.SessionLocal() as session:
            refreshed = (
                session.query(ExpenseModel)
                .options(
                    joinedload(ExpenseModel.splits),
                    joinedload(ExpenseModel.line_items),
                )
                .filter(ExpenseModel.id == expense_id)
                .first()
            )
            if not refreshed:
                return None

            splits = [
                SplitAllocation(
                    participantId=sr.participant_id,
                    amount=sr.amount,
                    percentage=sr.percentage,
                    shares=sr.shares,
                    computedBaseAmount=sr.computed_base_amount,
                )
                for sr in refreshed.splits
            ]

            line_items = [
                LineItem(
                    id=lr.id,
                    title=lr.title,
                    amount=lr.amount,
                    consumerIds=json.loads(lr.consumer_ids_json),
                )
                for lr in refreshed.line_items
            ] if refreshed.line_items else None

            return Expense(
                id=refreshed.id,
                eventId=refreshed.event_id,
                payerId=refreshed.payer_id,
                description=refreshed.description,
                originalAmount=refreshed.original_amount,
                originalCurrency=CurrencyCode(refreshed.original_currency),
                exchangeRate=refreshed.exchange_rate,
                baseAmount=refreshed.base_amount,
                isItemized=refreshed.is_itemized,
                date=refreshed.date,
                createdAt=refreshed.created_at,
                updatedAt=refreshed.updated_at,
                splits=splits,
                lineItems=line_items,
                taxAmount=refreshed.tax_amount,
                tipAmount=refreshed.tip_amount,
            )

    def delete_expense(self, event_id: str, expense_id: str, actor_id: str) -> bool:
        with self.SessionLocal() as session:
            exp = (
                session.query(ExpenseModel)
                .filter(ExpenseModel.id == expense_id, ExpenseModel.event_id == event_id)
                .first()
            )
            if not exp:
                return False

            description = exp.description
            session.delete(exp)

            created_at = now_iso()
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            act_details = json.dumps({
                "expenseId": expense_id,
                "description": description,
            })
            session.add(
                ActivityLogModel(
                    id=act_id,
                    event_id=event_id,
                    actor_id=actor_id,
                    action=ActivityAction.EXPENSE_DELETED.value,
                    details_json=act_details,
                    created_at=created_at,
                )
            )
            session.commit()
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

        act_id = f"act-{uuid.uuid4().hex[:8]}"
        act_details = json.dumps({
            "settlementId": set_id,
            "fromParticipantId": input_data.fromParticipantId,
            "toParticipantId": input_data.toParticipantId,
            "amount": input_data.amount,
        })

        with self.SessionLocal() as session:
            set_model = SettlementModel(
                id=settlement.id,
                event_id=settlement.eventId,
                from_participant_id=settlement.fromParticipantId,
                to_participant_id=settlement.toParticipantId,
                amount=settlement.amount,
                currency=settlement.currency.value,
                date=settlement.date,
                created_at=settlement.createdAt,
            )
            session.add(set_model)

            session.add(
                ActivityLogModel(
                    id=act_id,
                    event_id=event_id,
                    actor_id=input_data.fromParticipantId,
                    action=ActivityAction.SETTLEMENT_RECORDED.value,
                    details_json=act_details,
                    created_at=created_at,
                )
            )
            session.commit()

        return settlement


mock_db = SqliteDatabase()


def get_db() -> SqliteDatabase:
    return mock_db
