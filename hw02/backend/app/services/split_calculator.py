from typing import List, Dict, Optional, Sequence
import math
from app.schemas import SplitAllocation, SplitInput, SplitType, LineItemInput


def calculate_equal_split(
    base_amount: float,
    participant_ids: Sequence[str]
) -> List[SplitAllocation]:
    """
    Split an amount equally among participants, allocating cents fairly to avoid rounding loss.
    """
    if not participant_ids or base_amount <= 0:
        return [SplitAllocation(participantId=pid, computedBaseAmount=0.0) for pid in participant_ids]

    count = len(participant_ids)
    total_cents = round(base_amount * 100)
    base_cents = total_cents // count
    remainder = total_cents % count

    allocations: List[SplitAllocation] = []
    for pid in participant_ids:
        cents = base_cents + (1 if remainder > 0 else 0)
        if remainder > 0:
            remainder -= 1
        allocations.append(
            SplitAllocation(
                participantId=pid,
                computedBaseAmount=round(cents / 100.0, 2),
            )
        )
    return allocations


def calculate_exact_split(
    raw_splits: Sequence[SplitInput],
    exchange_rate: float
) -> List[SplitAllocation]:
    """
    Split by exact specified amounts per participant.
    """
    allocations: List[SplitAllocation] = []
    for s in raw_splits:
        amt = s.amount or 0.0
        allocations.append(
            SplitAllocation(
                participantId=s.participantId,
                amount=amt,
                computedBaseAmount=round(amt * exchange_rate, 2),
            )
        )
    return allocations


def calculate_percentage_split(
    base_amount: float,
    raw_splits: Sequence[SplitInput]
) -> List[SplitAllocation]:
    """
    Split by percentage allocation.
    """
    allocations: List[SplitAllocation] = []
    total_cents = round(base_amount * 100)
    allocated_cents = 0

    splits_list = list(raw_splits)
    for idx, s in enumerate(splits_list):
        pct = s.percentage or 0.0
        if idx == len(splits_list) - 1 and len(splits_list) > 1:
            # Last person absorbs minor cent rounding diff
            cents = total_cents - allocated_cents
        else:
            cents = round((pct / 100.0) * total_cents)
            allocated_cents += cents

        allocations.append(
            SplitAllocation(
                participantId=s.participantId,
                percentage=pct,
                computedBaseAmount=round(cents / 100.0, 2),
            )
        )
    return allocations


def calculate_shares_split(
    base_amount: float,
    raw_splits: Sequence[SplitInput]
) -> List[SplitAllocation]:
    """
    Split by relative shares allocation.
    """
    total_shares = sum(s.shares or 1.0 for s in raw_splits) or 1.0
    total_cents = round(base_amount * 100)
    allocated_cents = 0

    allocations: List[SplitAllocation] = []
    splits_list = list(raw_splits)
    for idx, s in enumerate(splits_list):
        sh = s.shares if s.shares is not None else 1.0
        if idx == len(splits_list) - 1 and len(splits_list) > 1:
            cents = total_cents - allocated_cents
        else:
            cents = round((sh / total_shares) * total_cents)
            allocated_cents += cents

        allocations.append(
            SplitAllocation(
                participantId=s.participantId,
                shares=sh,
                computedBaseAmount=round(cents / 100.0, 2),
            )
        )
    return allocations


def calculate_itemized_split(
    line_items: Sequence[LineItemInput],
    tax_amount: Optional[float],
    tip_amount: Optional[float],
    exchange_rate: float
) -> List[SplitAllocation]:
    """
    Itemized split with proportional tax and tip allocation based on consumed items.
    """
    subtotal = sum(item.amount for item in line_items)
    tax = tax_amount or 0.0
    tip = tip_amount or 0.0
    participant_shares: Dict[str, float] = {}

    for item in line_items:
        if item.consumerIds:
            share = item.amount / len(item.consumerIds)
            for cid in item.consumerIds:
                participant_shares[cid] = participant_shares.get(cid, 0.0) + share

    allocations: List[SplitAllocation] = []
    for cid, raw_share in participant_shares.items():
        ratio = (raw_share / subtotal) if subtotal > 0 else 0.0
        itemized_orig = raw_share + (tax + tip) * ratio
        comp_base = round(itemized_orig * exchange_rate, 2)
        allocations.append(
            SplitAllocation(
                participantId=cid,
                amount=round(itemized_orig, 2),
                computedBaseAmount=comp_base,
            )
        )
    return allocations


def compute_expense_splits(
    base_amount: float,
    exchange_rate: float,
    is_itemized: bool,
    split_type: Optional[SplitType] = None,
    splits: Optional[Sequence[SplitInput]] = None,
    line_items: Optional[Sequence[LineItemInput]] = None,
    tax_amount: Optional[float] = None,
    tip_amount: Optional[float] = None,
    fallback_participant_ids: Optional[Sequence[str]] = None,
) -> List[SplitAllocation]:
    """
    Unified entry point to compute splits for both creation and update operations.
    """
    if is_itemized and line_items:
        return calculate_itemized_split(
            line_items=line_items,
            tax_amount=tax_amount,
            tip_amount=tip_amount,
            exchange_rate=exchange_rate,
        )

    raw_splits = list(splits) if splits else []
    if not raw_splits and fallback_participant_ids:
        raw_splits = [SplitInput(participantId=pid) for pid in fallback_participant_ids]

    st = split_type or SplitType.EQUAL

    if st == SplitType.EQUAL:
        pids = [s.participantId for s in raw_splits]
        return calculate_equal_split(base_amount, pids)
    elif st == SplitType.EXACT:
        return calculate_exact_split(raw_splits, exchange_rate)
    elif st == SplitType.PERCENTAGE:
        return calculate_percentage_split(base_amount, raw_splits)
    elif st == SplitType.SHARES:
        return calculate_shares_split(base_amount, raw_splits)

    pids = [s.participantId for s in raw_splits]
    return calculate_equal_split(base_amount, pids)
