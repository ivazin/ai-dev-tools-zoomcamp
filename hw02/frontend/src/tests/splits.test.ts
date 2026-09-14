import { describe, it, expect } from 'vitest';
import {
  calculateEqualSplit,
  calculateExactSplit,
  calculateSharesSplit,
  calculateItemizedSplit,
  validateExactSplit,
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

  describe('Exact Split Validation & Assistance', () => {
    it('validates exact match correctly', () => {
      const result = validateExactSplit(100, {
        p1: 60,
        p2: 40,
      });

      expect(result.isValid).toBe(true);
      expect(result.totalAllocated).toBe(100);
      expect(result.remainingAmount).toBe(0);
      expect(result.difference).toBe(0);
    });

    it('detects under-allocated exact sums and indicates remaining amount', () => {
      const result = validateExactSplit(100, {
        p1: 45.5,
        p2: 20,
      });

      expect(result.isValid).toBe(false);
      expect(result.totalAllocated).toBe(65.5);
      expect(result.remainingAmount).toBe(34.5);
    });

    it('detects over-allocated exact sums', () => {
      const result = validateExactSplit(50, {
        p1: 30,
        p2: 25,
      });

      expect(result.isValid).toBe(false);
      expect(result.totalAllocated).toBe(55);
      expect(result.remainingAmount).toBe(-5);
    });
  });
});
