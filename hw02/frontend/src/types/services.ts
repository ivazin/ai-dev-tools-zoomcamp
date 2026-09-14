import {
  CurrencyCode,
  EventData,
  CreateEventInput,
  CreateExpenseInput,
  Expense,
  CreateSettlementInput,
  Settlement,
  Participant,
} from './index';

export type RealtimeEventType =
  | 'PARTICIPANT_ADDED'
  | 'EXPENSE_CREATED'
  | 'EXPENSE_UPDATED'
  | 'EXPENSE_DELETED'
  | 'SETTLEMENT_RECORDED'
  | 'RATES_UPDATED'
  | 'PRESENCE_CHANGE';

export interface RealtimeMessage<T = unknown> {
  type: RealtimeEventType;
  actorId?: string;
  timestamp: string;
  payload: T;
}

export type RealtimeSubscriber = (msg: RealtimeMessage) => void;

export interface IApiService {
  getEvent(eventId: string): Promise<EventData>;
  createEvent(input: CreateEventInput): Promise<EventData>;
  addParticipant(eventId: string, name: string): Promise<Participant>;
  createExpense(input: CreateExpenseInput): Promise<Expense>;
  updateExpense(expenseId: string, input: Partial<CreateExpenseInput>): Promise<Expense>;
  deleteExpense(eventId: string, expenseId: string, actorId: string): Promise<void>;
  createSettlement(input: CreateSettlementInput): Promise<Settlement>;
  getExchangeRate(fromCurrency: CurrencyCode, toCurrency: CurrencyCode, date?: string): Promise<{ rate: number; date: string }>;
}

export interface IRealtimeService {
  connect(eventId: string, participantId: string): void;
  disconnect(): void;
  subscribe(callback: RealtimeSubscriber): () => void;
  getOnlineParticipants(): string[];
}
