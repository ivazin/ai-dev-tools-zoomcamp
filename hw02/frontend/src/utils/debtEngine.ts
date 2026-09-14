import {
  Participant,
  Expense,
  Settlement,
  ParticipantBalance,
  DebtTransfer,
} from '../types';

/**
 * 7.1 Net Balance Calculation:
 * Balance(p) = PaidAsPayer(p) + ReceivedInSettlement(p) - OwedAsDebtor(p) - PaidInSettlement(p)
 */
export function calculateNetBalances(
  participants: Participant[],
  expenses: Expense[],
  settlements: Settlement[]
): ParticipantBalance[] {
  const balanceMap = new Map<string, { paid: number; owed: number }>();

  // Initialize
  participants.forEach((p) => {
    balanceMap.set(p.id, { paid: 0, owed: 0 });
  });

  // 1. Process Expenses
  for (const exp of expenses) {
    // Payer paid baseAmount
    const payerStats = balanceMap.get(exp.payerId);
    if (payerStats) {
      payerStats.paid += exp.baseAmount;
    }

    // Debtors owe their computedBaseAmount
    for (const split of exp.splits) {
      const debtorStats = balanceMap.get(split.participantId);
      if (debtorStats) {
        debtorStats.owed += split.computedBaseAmount;
      }
    }
  }

  // 2. Process Settlements
  for (const set of settlements) {
    // fromParticipant paid the settlement (reduces their debt, equivalent to paying an expense)
    const fromStats = balanceMap.get(set.fromParticipantId);
    if (fromStats) {
      fromStats.paid += set.amount;
    }

    // toParticipant received the settlement (reduces what is owed to them)
    const toStats = balanceMap.get(set.toParticipantId);
    if (toStats) {
      toStats.owed += set.amount;
    }
  }

  // 3. Assemble results rounded to 2 decimals
  return participants.map((p) => {
    const stats = balanceMap.get(p.id) || { paid: 0, owed: 0 };
    const net = Math.round((stats.paid - stats.owed) * 100) / 100;
    return {
      participantId: p.id,
      totalPaid: Math.round(stats.paid * 100) / 100,
      totalOwed: Math.round(stats.owed * 100) / 100,
      netBalance: net,
    };
  });
}

/**
 * 7.2 Simplified Debt Minimization (Greedy Heuristic):
 * Reduces transaction count by matching largest debtor with largest creditor.
 */
export function calculateSimplifiedDebts(balances: ParticipantBalance[]): DebtTransfer[] {
  // Separate into debtors (balance < -0.005) and creditors (balance > 0.005)
  const debtors: { id: string; balance: number }[] = [];
  const creditors: { id: string; balance: number }[] = [];

  for (const b of balances) {
    if (b.netBalance < -0.005) {
      debtors.push({ id: b.participantId, balance: b.netBalance });
    } else if (b.netBalance > 0.005) {
      creditors.push({ id: b.participantId, balance: b.netBalance });
    }
  }

  // Sort debtors ascending (e.g. -50 before -20)
  debtors.sort((a, b) => a.balance - b.balance);
  // Sort creditors descending (e.g. +60 before +10)
  creditors.sort((a, b) => b.balance - a.balance);

  const transfers: DebtTransfer[] = [];
  let dIdx = 0;
  let cIdx = 0;

  while (dIdx < debtors.length && cIdx < creditors.length) {
    const debtor = debtors[dIdx];
    const creditor = creditors[cIdx];

    const amountOwed = Math.abs(debtor.balance);
    const amountToReceive = creditor.balance;

    const transferAmount = Math.min(amountOwed, amountToReceive);
    const roundedTransfer = Math.round(transferAmount * 100) / 100;

    if (roundedTransfer > 0.005) {
      transfers.push({
        fromParticipantId: debtor.id,
        toParticipantId: creditor.id,
        amount: roundedTransfer,
      });
    }

    debtor.balance += roundedTransfer;
    creditor.balance -= roundedTransfer;

    if (Math.abs(debtor.balance) < 0.005) {
      dIdx++;
    }
    if (Math.abs(creditor.balance) < 0.005) {
      cIdx++;
    }
  }

  return transfers;
}

/**
 * 7.3 Direct / Pairwise Debt Calculation:
 * Bilateral debts without transitive transfers.
 */
export function calculatePairwiseDebts(
  participants: Participant[],
  expenses: Expense[],
  settlements: Settlement[]
): DebtTransfer[] {
  // Direct debt matrix: owes[A][B] is amount A directly owes B
  const matrix = new Map<string, Map<string, number>>();

  participants.forEach((p1) => {
    const row = new Map<string, number>();
    participants.forEach((p2) => {
      row.set(p2.id, 0);
    });
    matrix.set(p1.id, row);
  });

  // Accrue expenses
  for (const exp of expenses) {
    const payer = exp.payerId;
    for (const split of exp.splits) {
      const debtor = split.participantId;
      if (debtor !== payer) {
        const current = matrix.get(debtor)?.get(payer) || 0;
        matrix.get(debtor)?.set(payer, current + split.computedBaseAmount);
      }
    }
  }

  // Deduct settlements
  for (const set of settlements) {
    const debtor = set.fromParticipantId;
    const creditor = set.toParticipantId;
    const current = matrix.get(debtor)?.get(creditor) || 0;
    matrix.get(debtor)?.set(creditor, current - set.amount);
  }

  // Net pairwise debts between (i, j)
  const transfers: DebtTransfer[] = [];
  const visited = new Set<string>();

  for (const p1 of participants) {
    for (const p2 of participants) {
      if (p1.id === p2.id) continue;
      const pairKey = [p1.id, p2.id].sort().join(':');
      if (visited.has(pairKey)) continue;
      visited.add(pairKey);

      const p1OwesP2 = matrix.get(p1.id)?.get(p2.id) || 0;
      const p2OwesP1 = matrix.get(p2.id)?.get(p1.id) || 0;
      const net = Math.round((p1OwesP2 - p2OwesP1) * 100) / 100;

      if (net > 0.005) {
        transfers.push({
          fromParticipantId: p1.id,
          toParticipantId: p2.id,
          amount: net,
        });
      } else if (net < -0.005) {
        transfers.push({
          fromParticipantId: p2.id,
          toParticipantId: p1.id,
          amount: Math.abs(net),
        });
      }
    }
  }

  return transfers;
}
