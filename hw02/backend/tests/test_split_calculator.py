import pytest
from app.schemas import SplitType, SplitInput, LineItemInput
from app.services.split_calculator import (
    calculate_equal_split,
    calculate_exact_split,
    calculate_percentage_split,
    calculate_shares_split,
    calculate_itemized_split,
    compute_expense_splits,
)


def test_equal_split_even():
    splits = calculate_equal_split(60.0, ["p1", "p2", "p3"])
    assert len(splits) == 3
    assert all(s.computedBaseAmount == 20.0 for s in splits)


def test_equal_split_penny_distribution():
    # 100 EUR among 3 participants = 33.34 + 33.33 + 33.33 = 100.00
    splits = calculate_equal_split(100.0, ["p1", "p2", "p3"])
    amounts = [s.computedBaseAmount for s in splits]
    assert sum(amounts) == 100.0
    assert amounts == [33.34, 33.33, 33.33]


def test_exact_split():
    raw = [
        SplitInput(participantId="p1", amount=15.5),
        SplitInput(participantId="p2", amount=24.5),
    ]
    splits = calculate_exact_split(raw, exchange_rate=1.0)
    assert splits[0].computedBaseAmount == 15.5
    assert splits[1].computedBaseAmount == 24.5


def test_percentage_split():
    raw = [
        SplitInput(participantId="p1", percentage=60.0),
        SplitInput(participantId="p2", percentage=40.0),
    ]
    splits = calculate_percentage_split(50.0, raw)
    assert splits[0].computedBaseAmount == 30.0
    assert splits[1].computedBaseAmount == 20.0


def test_shares_split():
    raw = [
        SplitInput(participantId="p1", shares=2.0),
        SplitInput(participantId="p2", shares=1.0),
    ]
    splits = calculate_shares_split(90.0, raw)
    assert splits[0].computedBaseAmount == 60.0
    assert splits[1].computedBaseAmount == 30.0


def test_itemized_split():
    items = [
        LineItemInput(title="Burger", amount=10.0, consumerIds=["p1"]),
        LineItemInput(title="Pizza", amount=20.0, consumerIds=["p2"]),
        LineItemInput(title="Wine", amount=10.0, consumerIds=["p1", "p2"]),
    ]
    # Total items = 40. Tax = 4 (10%). Tip = 0.
    # p1: 10 + 5 = 15 -> with tax = 16.5
    # p2: 20 + 5 = 25 -> with tax = 27.5
    splits = calculate_itemized_split(items, tax_amount=4.0, tip_amount=0.0, exchange_rate=1.0)
    assert len(splits) == 2
    p1 = next(s for s in splits if s.participantId == "p1")
    p2 = next(s for s in splits if s.participantId == "p2")
    assert p1.computedBaseAmount == 16.5
    assert p2.computedBaseAmount == 27.5
