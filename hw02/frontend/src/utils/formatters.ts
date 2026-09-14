import { CurrencyCode } from '../types';
import { CURRENCY_SYMBOLS } from '../services/currencyRates';

export function formatMoney(amount: number, currency: CurrencyCode = 'EUR'): string {
  const symbol = CURRENCY_SYMBOLS[currency] || currency;
  const fixed = Math.abs(amount).toFixed(2);
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parseFloat(fixed));

  if (currency === 'EUR') {
    return amount < 0 ? `-€${formatted}` : `€${formatted}`;
  }
  return amount < 0 ? `-${symbol}${formatted}` : `${symbol}${formatted}`;
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 45) return 'just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function formatExpenseDate(dateStr: string, createdAt?: string): string {
  if (!dateStr) return '';

  const now = new Date();
  const expenseDate = new Date(dateStr);

  // Check if expense date is today (calendar day in local time)
  const isToday =
    expenseDate.getFullYear() === now.getFullYear() &&
    expenseDate.getMonth() === now.getMonth() &&
    expenseDate.getDate() === now.getDate();

  if (isToday) {
    // If we have createdAt timestamp that was just created, show relative time
    if (createdAt) {
      const createdDate = new Date(createdAt);
      const diffMs = now.getTime() - createdDate.getTime();
      const diffMin = Math.floor(diffMs / 60000);
      if (diffMin < 60) {
        return formatRelativeTime(createdAt);
      }
    }
    return 'Today';
  }

  // Check if yesterday
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const isYesterday =
    expenseDate.getFullYear() === yesterday.getFullYear() &&
    expenseDate.getMonth() === yesterday.getMonth() &&
    expenseDate.getDate() === yesterday.getDate();

  if (isYesterday) {
    return 'Yesterday';
  }

  return expenseDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function generateColor(name: string): string {
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
    '#8B5CF6', '#EC4899', '#06B6D4', '#14B8A6'
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % colors.length;
  return colors[index];
}
