import { describe, it, expect, beforeEach } from 'vitest';
import { MockApiService } from '../services/mockService';

describe('Centralized Mock Service Layer', () => {
  let service: MockApiService;

  beforeEach(() => {
    service = new MockApiService();
  });

  it('loads sample event and participants correctly', async () => {
    const event = await service.getEvent('barcelona-trip-2026');
    expect(event).toBeDefined();
    expect(event.title).toBe('Barcelona Getaway');
    expect(event.participants.length).toBe(4);
    expect(event.baseCurrency).toBe('EUR');
  });

  it('creates a new event with initial participants and creator', async () => {
    const newEvent = await service.createEvent({
      title: 'Rome Trip',
      baseCurrency: 'EUR',
      creatorName: 'Marco',
      initialParticipants: ['Giulia', 'Luca'],
    });

    expect(newEvent.id).toBeDefined();
    expect(newEvent.title).toBe('Rome Trip');
    expect(newEvent.participants.length).toBe(3);
    expect(newEvent.participants.map((p) => p.name)).toContain('Marco');
    expect(newEvent.participants.map((p) => p.name)).toContain('Giulia');
  });

  it('records expenses, updates audit activity logs, and converts multi-currency via ECB rate', async () => {
    const event = await service.getEvent('barcelona-trip-2026');
    const payer = event.participants[0];

    const expense = await service.createExpense({
      eventId: event.id,
      payerId: payer.id,
      description: 'Coffee and Croissants',
      originalAmount: 10,
      originalCurrency: 'USD',
      isItemized: false,
    });

    expect(expense.id).toBeDefined();
    expect(expense.description).toBe('Coffee and Croissants');
    // USD to EUR exchange rate applied
    expect(expense.baseAmount).toBeLessThan(10);
    expect(expense.baseAmount).toBeGreaterThan(8);

    const updatedEvent = await service.getEvent('barcelona-trip-2026');
    const latestLog = updatedEvent.activityLogs[0];
    expect(latestLog.action).toBe('EXPENSE_CREATED');
  });

  it('records a settlement and broadcasts update', async () => {
    const event = await service.getEvent('barcelona-trip-2026');
    const p1 = event.participants[0];
    const p2 = event.participants[1];

    const settlement = await service.createSettlement({
      eventId: event.id,
      fromParticipantId: p1.id,
      toParticipantId: p2.id,
      amount: 25.0,
    });

    expect(settlement.amount).toBe(25.0);
    expect(settlement.fromParticipantId).toBe(p1.id);
    expect(settlement.toParticipantId).toBe(p2.id);

    const updatedEvent = await service.getEvent('barcelona-trip-2026');
    expect(updatedEvent.settlements.some((s) => s.id === settlement.id)).toBe(true);
  });

  it('updates an existing expense and records an activity log entry', async () => {
    const event = await service.getEvent('barcelona-trip-2026');
    const expToUpdate = event.expenses[0];

    const updated = await service.updateExpense(expToUpdate.id, {
      description: 'Updated Airbnb Luxury Villa',
      originalAmount: 520,
      originalCurrency: 'EUR',
    });

    expect(updated.id).toBe(expToUpdate.id);
    expect(updated.description).toBe('Updated Airbnb Luxury Villa');
    expect(updated.baseAmount).toBe(520);

    const refreshedEvent = await service.getEvent('barcelona-trip-2026');
    const matched = refreshedEvent.expenses.find((e) => e.id === expToUpdate.id);
    expect(matched?.description).toBe('Updated Airbnb Luxury Villa');

    const latestLog = refreshedEvent.activityLogs[0];
    expect(latestLog.action).toBe('EXPENSE_UPDATED');
    expect(latestLog.details.description).toBe('Updated Airbnb Luxury Villa');
  });
});
