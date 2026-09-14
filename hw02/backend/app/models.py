from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    base_currency = Column(String(3), nullable=False)
    created_at = Column(String(64), nullable=False)

    participants = relationship("ParticipantModel", back_populates="event", cascade="all, delete-orphan")
    expenses = relationship("ExpenseModel", back_populates="event", cascade="all, delete-orphan")
    settlements = relationship("SettlementModel", back_populates="event", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLogModel", back_populates="event", cascade="all, delete-orphan")


class ParticipantModel(Base):
    __tablename__ = "participants"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    avatar_color = Column(String(16), nullable=False)
    created_at = Column(String(64), nullable=False)

    event = relationship("EventModel", back_populates="participants")


class ExpenseModel(Base):
    __tablename__ = "expenses"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    payer_id = Column(String(64), ForeignKey("participants.id"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    original_amount = Column(Float, nullable=False)
    original_currency = Column(String(3), nullable=False)
    exchange_rate = Column(Float, nullable=False)
    base_amount = Column(Float, nullable=False)
    is_itemized = Column(Boolean, default=False, nullable=False)
    category = Column(String(64), nullable=True)
    date = Column(String(64), nullable=False)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)
    tax_amount = Column(Float, nullable=True)
    tip_amount = Column(Float, nullable=True)

    event = relationship("EventModel", back_populates="expenses")
    payer = relationship("ParticipantModel")
    splits = relationship("ExpenseSplitModel", back_populates="expense", cascade="all, delete-orphan")
    line_items = relationship("LineItemModel", back_populates="expense", cascade="all, delete-orphan")


class ExpenseSplitModel(Base):
    __tablename__ = "expense_splits"

    id = Column(String(64), primary_key=True, index=True)
    expense_id = Column(String(64), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id = Column(String(64), ForeignKey("participants.id"), nullable=False, index=True)
    amount = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    shares = Column(Float, nullable=True)
    computed_base_amount = Column(Float, nullable=False)

    expense = relationship("ExpenseModel", back_populates="splits")
    participant = relationship("ParticipantModel")


class LineItemModel(Base):
    __tablename__ = "line_items"

    id = Column(String(64), primary_key=True, index=True)
    expense_id = Column(String(64), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    consumer_ids_json = Column(Text, nullable=False)  # JSON array of participant IDs

    expense = relationship("ExpenseModel", back_populates="line_items")


class SettlementModel(Base):
    __tablename__ = "settlements"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    from_participant_id = Column(String(64), ForeignKey("participants.id"), nullable=False, index=True)
    to_participant_id = Column(String(64), ForeignKey("participants.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    date = Column(String(64), nullable=False)
    created_at = Column(String(64), nullable=False)

    event = relationship("EventModel", back_populates="settlements")
    from_participant = relationship("ParticipantModel", foreign_keys=[from_participant_id])
    to_participant = relationship("ParticipantModel", foreign_keys=[to_participant_id])


class ActivityLogModel(Base):
    __tablename__ = "activity_logs"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(64), ForeignKey("participants.id"), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    details_json = Column(Text, nullable=False)  # JSON object
    created_at = Column(String(64), nullable=False)

    event = relationship("EventModel", back_populates="activity_logs")
    actor = relationship("ParticipantModel")
