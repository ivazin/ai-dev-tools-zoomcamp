import { SplitAllocation, LineItem } from '../types';

/**
 * Split an amount equally among participants, allocating cents fairly to avoid rounding loss.
 */
export function calculateEqualSplit(
  totalAmount: number,
  participantIds: string[]
): SplitAllocation[] {
  if (!participantIds.length || totalAmount <= 0) return [];

  const count = participantIds.length;
  const totalCents = Math.round(totalAmount * 100);
  const baseCents = Math.floor(totalCents / count);
  let remainder = totalCents % count;

  return participantIds.map((id) => {
    // Distribute remainder 1 cent at a time
    const cents = baseCents + (remainder > 0 ? 1 : 0);
    if (remainder > 0) remainder--;

    return {
      participantId: id,
      computedBaseAmount: cents / 100,
    };
  });
}

/**
 * Split by exact custom amounts per participant.
 */
export function calculateExactSplit(
  exacts: Record<string, number>
): SplitAllocation[] {
  return Object.entries(exacts).map(([participantId, amount]) => ({
    participantId,
    amount: Math.round(amount * 100) / 100,
    computedBaseAmount: Math.round(amount * 100) / 100,
  }));
}

/**
 * Split by percentage or shares.
 */
export function calculateSharesSplit(
  totalAmount: number,
  shares: Record<string, number>
): SplitAllocation[] {
  const totalShares = Object.values(shares).reduce((sum, s) => sum + Math.max(0, s), 0);
  if (totalShares <= 0 || totalAmount <= 0) return [];

  const totalCents = Math.round(totalAmount * 100);
  let allocatedCents = 0;
  const entries = Object.entries(shares).filter(([, s]) => s > 0);

  const splits: SplitAllocation[] = entries.map(([participantId, s], idx) => {
    if (idx === entries.length - 1) {
      // Last person absorbs rounding to guarantee exact total
      const cents = totalCents - allocatedCents;
      return {
        participantId,
        shares: s,
        computedBaseAmount: cents / 100,
      };
    }
    const cents = Math.round((s / totalShares) * totalCents);
    allocatedCents += cents;
    return {
      participantId,
      shares: s,
      computedBaseAmount: cents / 100,
    };
  });

  return splits;
}

/**
 * Itemized Receipt Split:
 * 1. Each line item is split evenly among its assigned consumers.
 * 2. Tax and tip are distributed strictly proportionally based on each diner's subtotal share.
 */
export function calculateItemizedSplit(
  lineItems: LineItem[],
  taxAmount: number = 0,
  tipAmount: number = 0,
  exchangeRate: number = 1.0
): {
  splits: SplitAllocation[];
  subtotal: number;
  totalWithTaxAndTip: number;
  baseAmount: number;
} {
  const subtotalMap = new Map<string, number>();

  for (const item of lineItems) {
    if (!item.consumerIds.length || item.amount <= 0) continue;
    const splitItems = calculateEqualSplit(item.amount, item.consumerIds);
    for (const s of splitItems) {
      const cur = subtotalMap.get(s.participantId) || 0;
      subtotalMap.set(s.participantId, cur + s.computedBaseAmount);
    }
  }

  const subtotal = Array.from(subtotalMap.values()).reduce((sum, val) => sum + val, 0);
  const extraTotal = Math.max(0, taxAmount) + Math.max(0, tipAmount);
  const totalOriginal = subtotal + extraTotal;
  const baseAmount = Math.round(totalOriginal * exchangeRate * 100) / 100;

  const splits: SplitAllocation[] = [];
  const diners = Array.from(subtotalMap.entries());

  if (subtotal > 0 && diners.length > 0) {
    let allocatedBaseCents = 0;
    const totalBaseCents = Math.round(baseAmount * 100);

    diners.forEach(([participantId, dinerSubtotal], idx) => {
      // Proportional ratio of items consumed
      const ratio = dinerSubtotal / subtotal;
      if (idx === diners.length - 1) {
        // Last diner gets remaining cents to balance exactly
        const baseCents = totalBaseCents - allocatedBaseCents;
        splits.push({
          participantId,
          computedBaseAmount: baseCents / 100,
        });
      } else {
        const originalDinerTotal = dinerSubtotal + ratio * extraTotal;
        const baseCents = Math.round(originalDinerTotal * exchangeRate * 100);
        allocatedBaseCents += baseCents;
        splits.push({
          participantId,
          computedBaseAmount: baseCents / 100,
        });
      }
    });
  }

  return {
    splits,
    subtotal: Math.round(subtotal * 100) / 100,
    totalWithTaxAndTip: Math.round(totalOriginal * 100) / 100,
    baseAmount,
  };
}
