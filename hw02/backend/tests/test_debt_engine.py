from app.services.debt_engine import (
    calculate_net_balances,
    calculate_simplified_debts,
    ParticipantBalance,
)


def test_debt_engine_net_balances():
    participants = [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
    expenses = [
        {
            "payerId": "p1",
            "baseAmount": 90.0,
            "splits": [
                {"participantId": "p1", "computedBaseAmount": 30.0},
                {"participantId": "p2", "computedBaseAmount": 30.0},
                {"participantId": "p3", "computedBaseAmount": 30.0},
            ],
        }
    ]
    settlements = []
    balances = calculate_net_balances(participants, expenses, settlements)
    b_map = {b.participantId: b for b in balances}

    assert b_map["p1"].netBalance == 60.0
    assert b_map["p2"].netBalance == -30.0
    assert b_map["p3"].netBalance == -30.0


def test_debt_engine_simplified_transfers():
    balances = [
        ParticipantBalance(participantId="p1", totalPaid=90.0, totalOwed=30.0, netBalance=60.0),
        ParticipantBalance(participantId="p2", totalPaid=0.0, totalOwed=30.0, netBalance=-30.0),
        ParticipantBalance(participantId="p3", totalPaid=0.0, totalOwed=30.0, netBalance=-30.0),
    ]
    transfers = calculate_simplified_debts(balances)
    assert len(transfers) == 2
    assert all(t.toParticipantId == "p1" for t in transfers)
    assert sum(t.amount for t in transfers) == 60.0
