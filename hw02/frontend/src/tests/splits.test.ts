import { describe, it, expect } from 'vitest';
import {
  calculateEqualSplit,
  calculateExactSplit,
  calculateSharesSplit,
  calculateItemizedSplit,
} from '../utils/splits';
import { LineItem } from '../types';

describe('Split Calculation Engine', () => {
  it('splits equally with exact penny distribution', () => {
    // 100 EUR split among 3 people should be 33.34, 33.33, 33.33 => total exactly 100.00
    const splits = calculateEqualSplit(100, ['p1', 'p2', 'p3']);
    expect(splits.length).toBe(3);

    const sum = splits.reduce((acc, s) => acc + s.computedBaseAmount, 0);
    expect(Math.round(sum * 100) / 100).toBe(100);
    expect(splits[0].computedBaseAmount).toBe(33.34);
    expect(splits[1].computedBaseAmount).toBe(33.33);
    expect(splits[2].computedBaseAmount).toBe(33.33);
  });

  it('calculates weighted shares splits correctly', () => {
    // 100 EUR with shares: Alice 2, Bob 1, Charlie 1 (Total 4 shares)
    // Alice gets 50, Bob gets 25, Charlie gets 25
    const splits = calculateSharesSplit(100, { p1: 2, p2: 1, p3: 1 });
    const sum = splits.reduce((acc, s) => acc + s.computedBaseAmount, 0);

    expect(sum).toBe(100);
    expect(splits.find((s) => s.participantId === 'p1')?.computedBaseAmount).toBe(50);
    expect(splits.find((s) => s.participantId === 'p2')?.computedBaseAmount).toBe(25);
    expect(splits.find((s) => s.participantId === 'p3')?.computedBaseAmount).toBe(25);
  });

  it('calculates itemized receipts and distributes tax & tip proportionally', () => {
    // Line 1: Steak 40 EUR consumed by Alice
    // Line 2: Salad 10 EUR consumed by Bob
    // Subtotal: 50 EUR. Alice ratio: 40/50 = 80%, Bob ratio: 10/50 = 20%
    // Tax: 5 EUR, Tip: 5 EUR (Total extra: 10 EUR)
    // Alice extra: 8 EUR => Total Alice: 48 EUR
    // Bob extra: 2 EUR => Total Bob: 12 EUR
    // Grand total: 60 EUR
    const lineItems: LineItem[] = [
      { id: '1', title: 'Steak', amount: 40, consumerIds: ['alice'] },
      { id: '2', title: 'Salad', amount: 10, consumerIds: ['bob'] },
    ];

    const result = calculateItemizedSplit(lineItems, 5, 5, 1.0);

    expect(result.subtotal).toBe(50);
    expect(result.totalWithTaxAndTip).toBe(60);
    expect(result.baseAmount).toBe(60);

    const aliceSplit = result.splits.find((s) => s.participantId === 'alice');
    const bobSplit = result.splits.find((s) => s.participantId === 'bob');

    expect(aliceSplit?.computedBaseAmount).toBe(48);
    expect(bobSplit?.computedBaseAmount).toBe(12);
  });
});
