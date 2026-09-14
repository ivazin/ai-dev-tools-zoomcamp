import {
  CurrencyCode,
  EventData,
  CreateEventInput,
  CreateExpenseInput,
  Expense,
  CreateSettlementInput,
  Settlement,
  Participant,
  LineItem,
} from '../types';
import {
  IApiService,
  IRealtimeService,
  RealtimeSubscriber,
  RealtimeMessage,
} from '../types/services';
import { SAMPLE_EVENT } from './mockData';
import { calculateExchangeRate } from './currencyRates';
import { calculateEqualSplit, calculateItemizedSplit } from '../utils/splits';
import { generateColor } from '../utils/formatters';

const STORAGE_KEY = 'splitwave_events_store_v1';

class MockRealtimeService implements IRealtimeService {
  private subscribers = new Set<RealtimeSubscriber>();
  private onlineUsers = new Set<string>();
  private activeEventId: string | null = null;
  private currentParticipantId: string | null = null;

  connect(eventId: string, participantId: string): void {
    this.activeEventId = eventId;
    this.currentParticipantId = participantId;
    this.onlineUsers.add(participantId);

    // Simulate other participants being online
    if (eventId === SAMPLE_EVENT.id) {
      this.onlineUsers.add('p-max');
      this.onlineUsers.add('p-sarah');
    }

    this.broadcast({
      type: 'PRESENCE_CHANGE',
      timestamp: new Date().toISOString(),
      payload: { onlineParticipants: Array.from(this.onlineUsers) },
    });
  }

  disconnect(): void {
    if (this.currentParticipantId) {
      this.onlineUsers.delete(this.currentParticipantId);
    }
    this.broadcast({
      type: 'PRESENCE_CHANGE',
      timestamp: new Date().toISOString(),
      payload: { onlineParticipants: Array.from(this.onlineUsers) },
    });
    this.subscribers.clear();
    this.activeEventId = null;
    this.currentParticipantId = null;
  }

  subscribe(callback: RealtimeSubscriber): () => void {
    this.subscribers.add(callback);
    return () => {
      this.subscribers.delete(callback);
    };
  }

  getOnlineParticipants(): string[] {
    return Array.from(this.onlineUsers);
  }

  broadcast<T>(msg: RealtimeMessage<T>): void {
    this.subscribers.forEach((sub) => {
      try {
        sub(msg as unknown as RealtimeMessage);
      } catch (err) {
        console.error('WebSocket subscriber error:', err);
      }
    });
  }
}

export class MockApiService implements IApiService {
  private events: Map<string, EventData> = new Map();
  public realtime: MockRealtimeService;

  constructor(realtimeService?: MockRealtimeService) {
    this.realtime = realtimeService || new MockRealtimeService();
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Record<string, EventData>;
        Object.entries(parsed).forEach(([id, ev]) => {
          this.events.set(id, ev);
        });
      }
    } catch {
      // localStorage may not be available in non-browser or test env
    }

    // Always ensure SAMPLE_EVENT is available
    if (!this.events.has(SAMPLE_EVENT.id)) {
      this.events.set(SAMPLE_EVENT.id, JSON.parse(JSON.stringify(SAMPLE_EVENT)));
      this.saveToStorage();
    }
  }

  private saveToStorage(): void {
    try {
      const obj: Record<string, EventData> = {};
      this.events.forEach((val, key) => {
        obj[key] = val;
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(obj));
    } catch {
      // In-memory fallback
    }
  }

  private generateId(prefix: string): string {
    return `${prefix}-${Math.random().toString(36).substring(2, 9)}`;
  }

  async getEvent(eventId: string): Promise<EventData> {
    await new Promise((res) => setTimeout(res, 60)); // Simulate micro network latency
    const ev = this.events.get(eventId);
    if (!ev) {
      throw new Error(`Event with id "${eventId}" not found.`);
    }
    return JSON.parse(JSON.stringify(ev));
  }

  async createEvent(input: CreateEventInput): Promise<EventData> {
    await new Promise((res) => setTimeout(res, 80));
    const eventId = Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10);
    const now = new Date().toISOString();

    const creator: Participant = {
      id: this.generateId('p'),
      eventId,
      name: input.creatorName.trim(),
      avatarColor: generateColor(input.creatorName),
      createdAt: now,
    };

    const participants: Participant[] = [creator];

    for (const name of input.initialParticipants) {
      const trimmed = name.trim();
      if (trimmed && trimmed.toLowerCase() !== input.creatorName.trim().toLowerCase()) {
        participants.push({
          id: this.generateId('p'),
          eventId,
          name: trimmed,
          avatarColor: generateColor(trimmed),
          createdAt: now,
        });
      }
    }

    const newEvent: EventData = {
      id: eventId,
      title: input.title.trim(),
      baseCurrency: input.baseCurrency,
      createdAt: now,
      participants,
      expenses: [],
      settlements: [],
      activityLogs: [
        {
          id: this.generateId('act'),
          eventId,
          actorId: creator.id,
          action: 'EVENT_CREATED',
          details: { title: input.title, baseCurrency: input.baseCurrency },
          createdAt: now,
        },
      ],
    };

    this.events.set(eventId, newEvent);
    this.saveToStorage();

    return JSON.parse(JSON.stringify(newEvent));
  }

  async addParticipant(eventId: string, name: string): Promise<Participant> {
    const ev = this.events.get(eventId);
    if (!ev) throw new Error('Event not found');

    const trimmed = name.trim();
    const existing = ev.participants.find((p) => p.name.toLowerCase() === trimmed.toLowerCase());
    if (existing) return existing;

    const participant: Participant = {
      id: this.generateId('p'),
      eventId,
      name: trimmed,
      avatarColor: generateColor(trimmed),
      createdAt: new Date().toISOString(),
    };

    ev.participants.push(participant);
    ev.activityLogs.unshift({
      id: this.generateId('act'),
      eventId,
      actorId: participant.id,
      action: 'PARTICIPANT_ADDED',
      details: { name: trimmed },
      createdAt: new Date().toISOString(),
    });

    this.saveToStorage();

    this.realtime.broadcast({
      type: 'PARTICIPANT_ADDED',
      actorId: participant.id,
      timestamp: new Date().toISOString(),
      payload: participant,
    });

    return participant;
  }

  async createExpense(input: CreateExpenseInput): Promise<Expense> {
    const ev = this.events.get(input.eventId);
    if (!ev) throw new Error('Event not found');

    const now = new Date().toISOString();
    const exchangeRate = calculateExchangeRate(input.originalCurrency, ev.baseCurrency);
    const baseAmount = Math.round(input.originalAmount * exchangeRate * 100) / 100;

    let splits: import('../types').SplitAllocation[] = input.splits?.map((s) => ({
      participantId: s.participantId,
      amount: s.amount,
      percentage: s.percentage,
      shares: s.shares,
      computedBaseAmount: Math.round((s.amount || 0) * exchangeRate * 100) / 100,
    })) || [];

    let lineItems: LineItem[] | undefined = undefined;

    if (input.isItemized && input.lineItems && input.lineItems.length > 0) {
      lineItems = input.lineItems.map((li) => ({
        id: this.generateId('li'),
        title: li.title,
        amount: li.amount,
        consumerIds: li.consumerIds,
      }));

      const res = calculateItemizedSplit(
        lineItems,
        input.taxAmount || 0,
        input.tipAmount || 0,
        exchangeRate
      );
      splits = res.splits;
    } else if (!splits.length) {
      // Default: split equally among all participants
      const participantIds = ev.participants.map((p) => p.id);
      splits = calculateEqualSplit(baseAmount, participantIds);
    }

    const expense: Expense = {
      id: this.generateId('exp'),
      eventId: input.eventId,
      payerId: input.payerId,
      description: input.description.trim(),
      originalAmount: input.originalAmount,
      originalCurrency: input.originalCurrency,
      exchangeRate,
      baseAmount,
      isItemized: input.isItemized,
      date: input.date || now,
      createdAt: now,
      updatedAt: now,
      splits,
      lineItems,
      taxAmount: input.taxAmount,
      tipAmount: input.tipAmount,
    };

    ev.expenses.unshift(expense);
    ev.activityLogs.unshift({
      id: this.generateId('act'),
      eventId: input.eventId,
      actorId: input.payerId,
      action: 'EXPENSE_CREATED',
      details: {
        description: expense.description,
        amount: expense.originalAmount,
        currency: expense.originalCurrency,
        baseAmount: expense.baseAmount,
        itemized: expense.isItemized,
      },
      createdAt: now,
    });

    this.saveToStorage();

    this.realtime.broadcast({
      type: 'EXPENSE_CREATED',
      actorId: input.payerId,
      timestamp: now,
      payload: expense,
    });

    return expense;
  }

  async updateExpense(expenseId: string, input: Partial<CreateExpenseInput>): Promise<Expense> {
    let targetEvent: EventData | undefined;
    let targetExp: Expense | undefined;

    for (const ev of this.events.values()) {
      const found = ev.expenses.find((e) => e.id === expenseId);
      if (found) {
        targetEvent = ev;
        targetExp = found;
        break;
      }
    }

    if (!targetEvent || !targetExp) throw new Error('Expense not found');

    const now = new Date().toISOString();
    const origCurr = input.originalCurrency || targetExp.originalCurrency;
    const origAmount = input.originalAmount !== undefined ? input.originalAmount : targetExp.originalAmount;
    const exchangeRate = calculateExchangeRate(origCurr, targetEvent.baseCurrency);
    const baseAmount = Math.round(origAmount * exchangeRate * 100) / 100;

    targetExp.description = input.description ? input.description.trim() : targetExp.description;
    targetExp.originalAmount = origAmount;
    targetExp.originalCurrency = origCurr;
    targetExp.exchangeRate = exchangeRate;
    targetExp.baseAmount = baseAmount;
    targetExp.payerId = input.payerId || targetExp.payerId;
    targetExp.updatedAt = now;

    targetEvent.activityLogs.unshift({
      id: this.generateId('act'),
      eventId: targetEvent.id,
      actorId: targetExp.payerId,
      action: 'EXPENSE_UPDATED',
      details: {
        description: targetExp.description,
        amount: targetExp.originalAmount,
        baseAmount: targetExp.baseAmount,
      },
      createdAt: now,
    });

    this.saveToStorage();

    this.realtime.broadcast({
      type: 'EXPENSE_UPDATED',
      actorId: targetExp.payerId,
      timestamp: now,
      payload: targetExp,
    });

    return targetExp;
  }

  async deleteExpense(eventId: string, expenseId: string, actorId: string): Promise<void> {
    const ev = this.events.get(eventId);
    if (!ev) throw new Error('Event not found');

    const idx = ev.expenses.findIndex((e) => e.id === expenseId);
    if (idx === -1) return;

    const [deleted] = ev.expenses.splice(idx, 1);
    const now = new Date().toISOString();

    ev.activityLogs.unshift({
      id: this.generateId('act'),
      eventId,
      actorId,
      action: 'EXPENSE_DELETED',
      details: { description: deleted.description, amount: deleted.baseAmount },
      createdAt: now,
    });

    this.saveToStorage();

    this.realtime.broadcast({
      type: 'EXPENSE_DELETED',
      actorId,
      timestamp: now,
      payload: { expenseId },
    });
  }

  async createSettlement(input: CreateSettlementInput): Promise<Settlement> {
    const ev = this.events.get(input.eventId);
    if (!ev) throw new Error('Event not found');

    const now = new Date().toISOString();
    const settlement: Settlement = {
      id: this.generateId('set'),
      eventId: input.eventId,
      fromParticipantId: input.fromParticipantId,
      toParticipantId: input.toParticipantId,
      amount: Math.round(input.amount * 100) / 100,
      currency: input.currency || ev.baseCurrency,
      date: input.date || now,
      createdAt: now,
    };

    ev.settlements.unshift(settlement);
    ev.activityLogs.unshift({
      id: this.generateId('act'),
      eventId: input.eventId,
      actorId: input.fromParticipantId,
      action: 'SETTLEMENT_RECORDED',
      details: {
        fromParticipantId: settlement.fromParticipantId,
        toParticipantId: settlement.toParticipantId,
        amount: settlement.amount,
        currency: settlement.currency,
      },
      createdAt: now,
    });

    this.saveToStorage();

    this.realtime.broadcast({
      type: 'SETTLEMENT_RECORDED',
      actorId: input.fromParticipantId,
      timestamp: now,
      payload: settlement,
    });

    return settlement;
  }

  async getExchangeRate(
    fromCurrency: CurrencyCode,
    toCurrency: CurrencyCode,
    date?: string
  ): Promise<{ rate: number; date: string }> {
    return {
      rate: calculateExchangeRate(fromCurrency, toCurrency),
      date: date || new Date().toISOString().split('T')[0],
    };
  }
}

export const mockRealtimeService = new MockRealtimeService();
export const mockApiService = new MockApiService(mockRealtimeService);
