export type CurrencyCode = 'EUR' | 'USD' | 'GBP' | 'JPY' | 'CAD' | 'CHF' | 'AUD';

export interface Participant {
  id: string;
  eventId: string;
  name: string;
  avatarColor: string;
  createdAt: string;
}

export type SplitType = 'EQUAL' | 'EXACT' | 'PERCENTAGE' | 'SHARES';

export interface SplitAllocation {
  participantId: string;
  amount?: number;        // For exact
  percentage?: number;    // For percentage
  shares?: number;        // For shares
  computedBaseAmount: number;
}

export interface LineItem {
  id: string;
  title: string;
  amount: number;
  consumerIds: string[];
}

export interface Expense {
  id: string;
  eventId: string;
  payerId: string;
  description: string;
  originalAmount: number;
  originalCurrency: CurrencyCode;
  exchangeRate: number;    // Multiplier to convert to base currency
  baseAmount: number;      // Amount in event base currency
  isItemized: boolean;
  category?: string;
  date: string;
  createdAt: string;
  updatedAt: string;
  // Splits
  splits: SplitAllocation[];
  // If itemized
  lineItems?: LineItem[];
  taxAmount?: number;
  tipAmount?: number;
}

export interface Settlement {
  id: string;
  eventId: string;
  fromParticipantId: string;
  toParticipantId: string;
  amount: number;          // In base currency
  currency: CurrencyCode;
  date: string;
  createdAt: string;
}

export interface ActivityLog {
  id: string;
  eventId: string;
  actorId: string;
  action: 'EVENT_CREATED' | 'PARTICIPANT_ADDED' | 'EXPENSE_CREATED' | 'EXPENSE_UPDATED' | 'EXPENSE_DELETED' | 'SETTLEMENT_RECORDED';
  details: Record<string, unknown>;
  createdAt: string;
}

export interface EventData {
  id: string;
  title: string;
  baseCurrency: CurrencyCode;
  createdAt: string;
  participants: Participant[];
  expenses: Expense[];
  settlements: Settlement[];
  activityLogs: ActivityLog[];
}

export interface DebtTransfer {
  fromParticipantId: string;
  toParticipantId: string;
  amount: number;
}

export interface ParticipantBalance {
  participantId: string;
  totalPaid: number;
  totalOwed: number;
  netBalance: number; // Positive means they are owed money, negative means they owe money
}

export interface CreateEventInput {
  title: string;
  baseCurrency: CurrencyCode;
  creatorName: string;
  initialParticipants: string[];
}

export interface CreateExpenseInput {
  eventId: string;
  payerId: string;
  description: string;
  originalAmount: number;
  originalCurrency: CurrencyCode;
  date?: string;
  isItemized: boolean;
  splits?: Array<{
    participantId: string;
    amount?: number;
    percentage?: number;
    shares?: number;
  }>;
  splitType?: SplitType;
  lineItems?: Array<{
    title: string;
    amount: number;
    consumerIds: string[];
  }>;
  taxAmount?: number;
  tipAmount?: number;
}

export interface CreateSettlementInput {
  eventId: string;
  fromParticipantId: string;
  toParticipantId: string;
  amount: number;
  currency?: CurrencyCode;
  date?: string;
}
