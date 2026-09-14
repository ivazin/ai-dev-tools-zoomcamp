import { describe, it, expect } from 'vitest';
import {
  calculateNetBalances,
  calculateSimplifiedDebts,
  calculatePairwiseDebts,
} from '../utils/debtEngine';
import { Participant, Expense, Settlement } from '../types';

describe('Debt Resolution Engine', () => {
  const participants: Participant[] = [
    { id: 'p1', eventId: 'e1', name: 'Alice', avatarColor: '#fff', createdAt: '' },
    { id: 'p2', eventId: 'e1', name: 'Bob', avatarColor: '#fff', createdAt: '' },
    { id: 'p3', eventId: 'e1', name: 'Charlie', avatarColor: '#fff', createdAt: '' },
  ];

  it('correctly calculates net balances from simple shared expenses', () => {
    // Alice pays 90 for Alice, Bob, Charlie (30 each)
    const expenses: Expense[] = [
      {
        id: 'exp1',
        eventId: 'e1',
        payerId: 'p1',
        description: 'Dinner',
        originalAmount: 90,
        originalCurrency: 'EUR',
        exchangeRate: 1.0,
        baseAmount: 90,
        isItemized: false,
        date: '',
        createdAt: '',
        updatedAt: '',
        splits: [
          { participantId: 'p1', computedBaseAmount: 30 },
          { participantId: 'p2', computedBaseAmount: 30 },
          { participantId: 'p3', computedBaseAmount: 30 },
        ],
      },
    ];

    const balances = calculateNetBalances(participants, expenses, []);

    const alice = balances.find((b) => b.participantId === 'p1');
    const bob = balances.find((b) => b.participantId === 'p2');
    const charlie = balances.find((b) => b.participantId === 'p3');

    // Alice paid 90, owes 30 => +60
    expect(alice?.netBalance).toBe(60);
    // Bob paid 0, owes 30 => -30
    expect(bob?.netBalance).toBe(-30);
    // Charlie paid 0, owes 30 => -30
    expect(charlie?.netBalance).toBe(-30);
  });

  it('minimizes transaction count with greedy debt simplification algorithm', () => {
    // Alice paid 60 for Bob (+60 Alice, -60 Bob)
    // Bob paid 40 for Charlie (+40 Bob, -40 Charlie)
    // Net: Alice +60, Bob -20, Charlie -40
    // Simplified output should route: Charlie pays Alice 40, Bob pays Alice 20 (Total 2 transfers)
    const balances = [
      { participantId: 'p1', totalPaid: 60, totalOwed: 0, netBalance: 60 },
      { participantId: 'p2', totalPaid: 40, totalOwed: 60, netBalance: -20 },
      { participantId: 'p3', totalPaid: 0, totalOwed: 40, netBalance: -40 },
    ];

    const transfers = calculateSimplifiedDebts(balances);

    expect(transfers.length).toBe(2);
    // Sum of transfers to Alice should equal 60
    const totalToAlice = transfers
      .filter((t) => t.toParticipantId === 'p1')
      .reduce((sum, t) => sum + t.amount, 0);
    expect(totalToAlice).toBe(60);
  });

  it('pairwise debt calculation maintains direct bilateral debt links', () => {
    const expenses: Expense[] = [
      {
        id: 'exp1',
        eventId: 'e1',
        payerId: 'p1',
        description: 'Alice for Bob',
        originalAmount: 50,
        originalCurrency: 'EUR',
        exchangeRate: 1.0,
        baseAmount: 50,
        isItemized: false,
        date: '',
        createdAt: '',
        updatedAt: '',
        splits: [{ participantId: 'p2', computedBaseAmount: 50 }],
      },
      {
        id: 'exp2',
        eventId: 'e1',
        payerId: 'p2',
        description: 'Bob for Alice',
        originalAmount: 20,
        originalCurrency: 'EUR',
        exchangeRate: 1.0,
        baseAmount: 20,
        isItemized: false,
        date: '',
        createdAt: '',
        updatedAt: '',
        splits: [{ participantId: 'p1', computedBaseAmount: 20 }],
      },
    ];

    // Net pairwise: Bob owes Alice 50 - 20 = 30
    const transfers = calculatePairwiseDebts(participants, expenses, []);
    expect(transfers.length).toBe(1);
    expect(transfers[0].fromParticipantId).toBe('p2');
    expect(transfers[0].toParticipantId).toBe('p1');
    expect(transfers[0].amount).toBe(30);
  });

  it('settlements offset outstanding balances correctly', () => {
    const expenses: Expense[] = [
      {
        id: 'exp1',
        eventId: 'e1',
        payerId: 'p1',
        description: 'Alice paid for Bob',
        originalAmount: 50,
        originalCurrency: 'EUR',
        exchangeRate: 1.0,
        baseAmount: 50,
        isItemized: false,
        date: '',
        createdAt: '',
        updatedAt: '',
        splits: [{ participantId: 'p2', computedBaseAmount: 50 }],
      },
    ];

    const settlements: Settlement[] = [
      {
        id: 'set1',
        eventId: 'e1',
        fromParticipantId: 'p2',
        toParticipantId: 'p1',
        amount: 50,
        currency: 'EUR',
        date: '',
        createdAt: '',
      },
    ];

    const balances = calculateNetBalances(participants, expenses, settlements);
    const alice = balances.find((b) => b.participantId === 'p1');
    const bob = balances.find((b) => b.participantId === 'p2');

    expect(alice?.netBalance).toBe(0);
    expect(bob?.netBalance).toBe(0);
  });
});
