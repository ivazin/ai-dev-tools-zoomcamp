from typing import List, Dict
from pydantic import BaseModel


class ParticipantBalance(BaseModel):
    participantId: str
    totalPaid: float
    totalOwed: float
    netBalance: float


class DebtTransfer(BaseModel):
    fromParticipantId: str
    toParticipantId: str
    amount: float


def calculate_net_balances(
    participants: List[dict],
    expenses: List[dict],
    settlements: List[dict]
) -> List[ParticipantBalance]:
    """
    Computes net balances for each participant:
    Balance(p) = PaidAsPayer(p) + ReceivedInSettlement(p) - OwedAsDebtor(p) - PaidInSettlement(p)
    """
    balance_map: Dict[str, Dict[str, float]] = {
        p["id"]: {"paid": 0.0, "owed": 0.0} for p in participants
    }

    for exp in expenses:
        payer_id = exp["payerId"]
        base_amt = exp["baseAmount"]
        if payer_id in balance_map:
            balance_map[payer_id]["paid"] += base_amt

        for split in exp.get("splits", []):
            debtor_id = split["participantId"]
            owed_amt = split["computedBaseAmount"]
            if debtor_id in balance_map:
                balance_map[debtor_id]["owed"] += owed_amt

    for st in settlements:
        from_id = st["fromParticipantId"]
        to_id = st["toParticipantId"]
        amt = st["amount"]
        if from_id in balance_map:
            balance_map[from_id]["paid"] += amt
        if to_id in balance_map:
            balance_map[to_id]["owed"] += amt

    results: List[ParticipantBalance] = []
    for p in participants:
        pid = p["id"]
        stats = balance_map.get(pid, {"paid": 0.0, "owed": 0.0})
        paid = round(stats["paid"], 2)
        owed = round(stats["owed"], 2)
        net = round(paid - owed, 2)
        results.append(
            ParticipantBalance(
                participantId=pid,
                totalPaid=paid,
                totalOwed=owed,
                netBalance=net,
            )
        )
    return results


def calculate_simplified_debts(balances: List[ParticipantBalance]) -> List[DebtTransfer]:
    """
    Greedy debt minimization algorithm matching largest debtor with largest creditor.
    """
    debtors: List[Dict[str, float]] = []
    creditors: List[Dict[str, float]] = []

    for b in balances:
        if b.netBalance < -0.005:
            debtors.append({"id": b.participantId, "balance": b.netBalance})
        elif b.netBalance > 0.005:
            creditors.append({"id": b.participantId, "balance": b.netBalance})

    debtors.sort(key=lambda x: x["balance"])  # Most negative first
    creditors.sort(key=lambda x: x["balance"], reverse=True)  # Most positive first

    transfers: List[DebtTransfer] = []
    d_idx = 0
    c_idx = 0

    while d_idx < len(debtors) and c_idx < len(creditors):
        debtor = debtors[d_idx]
        creditor = creditors[c_idx]

        amount_owed = abs(debtor["balance"])
        amount_credit = creditor["balance"]
        transfer_amount = min(amount_owed, amount_credit)

        if transfer_amount >= 0.01:
            transfers.append(
                DebtTransfer(
                    fromParticipantId=debtor["id"],
                    toParticipantId=creditor["id"],
                    amount=round(transfer_amount, 2),
                )
            )

        debtor["balance"] += transfer_amount
        creditor["balance"] -= transfer_amount

        if abs(debtor["balance"]) < 0.005:
            d_idx += 1
        if creditor["balance"] < 0.005:
            c_idx += 1

    return transfers
