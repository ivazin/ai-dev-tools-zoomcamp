import { CurrencyCode } from '../types';

// Reference rates to EUR based on European Central Bank data
export const ECB_RATES_TO_EUR: Record<CurrencyCode, number> = {
  EUR: 1.0,
  USD: 1.085,   // 1 EUR = 1.085 USD -> 1 USD = 1/1.085 EUR
  GBP: 0.855,   // 1 EUR = 0.855 GBP
  JPY: 162.4,   // 1 EUR = 162.4 JPY
  CAD: 1.472,   // 1 EUR = 1.472 CAD
  CHF: 0.958,   // 1 EUR = 0.958 CHF
  AUD: 1.645,   // 1 EUR = 1.645 AUD
};

export const CURRENCY_SYMBOLS: Record<CurrencyCode, string> = {
  EUR: '€',
  USD: '$',
  GBP: '£',
  JPY: '¥',
  CAD: 'CA$',
  CHF: 'CHF',
  AUD: 'AU$',
};

export function calculateExchangeRate(from: CurrencyCode, to: CurrencyCode): number {
  if (from === to) return 1.0;
  
  const fromRateToEur = ECB_RATES_TO_EUR[from] || 1.0;
  const toRateToEur = ECB_RATES_TO_EUR[to] || 1.0;

  // 1 unit of `from` = (1 / fromRateToEur) EUR = (toRateToEur / fromRateToEur) units of `to`
  const rate = toRateToEur / fromRateToEur;
  return Math.round(rate * 1000000) / 1000000;
}
