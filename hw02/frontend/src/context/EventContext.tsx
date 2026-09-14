import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  EventData,
  Participant,
  Expense,
  Settlement,
  ActivityLog,
  CreateEventInput,
  CreateExpenseInput,
  CreateSettlementInput,
} from '../types';
import services from '../services';
import { useToast } from './ToastContext';

interface EventContextType {
  event: EventData | null;
  activeParticipant: Participant | null;
  onlineParticipantIds: string[];
  isLoading: boolean;
  error: string | null;
  isMock: boolean;
  setActiveParticipant: (p: Participant) => void;
  loadEvent: (eventId: string) => Promise<void>;
  createEvent: (input: CreateEventInput) => Promise<string>;
  addParticipant: (name: string) => Promise<Participant>;
  createExpense: (input: CreateExpenseInput) => Promise<Expense>;
  updateExpense: (id: string, input: Partial<CreateExpenseInput>) => Promise<Expense>;
  deleteExpense: (id: string) => Promise<void>;
  createSettlement: (input: CreateSettlementInput) => Promise<Settlement>;
  lastUpdatedItemId: string | null;
}

const EventContext = createContext<EventContextType | undefined>(undefined);

const LOCAL_STORAGE_ACTIVE_USER = 'splitwave_active_user';

export const EventProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [event, setEvent] = useState<EventData | null>(null);
  const [activeParticipant, setActiveParticipantState] = useState<Participant | null>(null);
  const [onlineParticipantIds, setOnlineParticipantIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedItemId, setLastUpdatedItemId] = useState<string | null>(null);
  const { showToast } = useToast();

  const setActiveParticipant = useCallback((p: Participant) => {
    setActiveParticipantState(p);
    try {
      localStorage.setItem(`${LOCAL_STORAGE_ACTIVE_USER}_${p.eventId}`, JSON.stringify(p));
    } catch {
      // Ignore
    }
  }, []);

  const loadEvent = useCallback(async (eventId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await services.api.getEvent(eventId);
      setEvent(data);

      // Check saved participant in localStorage
      try {
        const saved = localStorage.getItem(`${LOCAL_STORAGE_ACTIVE_USER}_${eventId}`);
        if (saved) {
          const parsed = JSON.parse(saved) as Participant;
          const matched = data.participants.find((p) => p.id === parsed.id);
          if (matched) {
            setActiveParticipantState(matched);
          }
        }
      } catch {
        // Ignore
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load event');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Subscribe to real-time updates when event & participant are set
  useEffect(() => {
    if (!event || !activeParticipant) return;

    services.realtime.connect(event.id, activeParticipant.id);
    setOnlineParticipantIds(services.realtime.getOnlineParticipants());

    const unsubscribe = services.realtime.subscribe((msg) => {
      if (msg.type === 'PRESENCE_CHANGE') {
        const payload = msg.payload as { onlineParticipants: string[] };
        if (payload?.onlineParticipants) {
          setOnlineParticipantIds(payload.onlineParticipants);
        }
      } else if (msg.type === 'PARTICIPANT_ADDED') {
        const newP = msg.payload as Participant;
        setEvent((prev) => prev ? { ...prev, participants: [...prev.participants, newP] } : prev);
        showToast(`${newP.name} joined the event!`, 'info');
      } else if (msg.type === 'EXPENSE_CREATED') {
        const exp = msg.payload as Expense;
        setEvent((prev) => {
          if (!prev) return prev;
          if (prev.expenses.some((e) => e.id === exp.id)) return prev;
          return { ...prev, expenses: [exp, ...prev.expenses] };
        });
        setLastUpdatedItemId(exp.id);
        if (msg.actorId !== activeParticipant.id) {
          showToast(`New expense: "${exp.description}"`, 'info');
        }
      } else if (msg.type === 'EXPENSE_UPDATED') {
        const exp = msg.payload as Expense;
        setEvent((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            expenses: prev.expenses.map((e) => (e.id === exp.id ? exp : e)),
          };
        });
        setLastUpdatedItemId(exp.id);
        if (msg.actorId !== activeParticipant.id) {
          showToast(`Expense updated: "${exp.description}"`, 'info');
        }
      } else if (msg.type === 'EXPENSE_DELETED') {
        const { expenseId } = msg.payload as { expenseId: string };
        setEvent((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            expenses: prev.expenses.filter((e) => e.id !== expenseId),
          };
        });
      } else if (msg.type === 'SETTLEMENT_RECORDED') {
        const set = msg.payload as Settlement;
        setEvent((prev) => {
          if (!prev) return prev;
          if (prev.settlements.some((s) => s.id === set.id)) return prev;
          return { ...prev, settlements: [set, ...prev.settlements] };
        });
        showToast('Settlement recorded!', 'success');
      }
    });

    return () => {
      unsubscribe();
      services.realtime.disconnect();
    };
  }, [event?.id, activeParticipant?.id, showToast]);

  const createEvent = async (input: CreateEventInput): Promise<string> => {
    setIsLoading(true);
    try {
      const newEv = await services.api.createEvent(input);
      setEvent(newEv);
      if (newEv.participants.length > 0) {
        setActiveParticipant(newEv.participants[0]);
      }
      return newEv.id;
    } finally {
      setIsLoading(false);
    }
  };

  const addParticipant = async (name: string): Promise<Participant> => {
    if (!event) throw new Error('No active event');
    const p = await services.api.addParticipant(event.id, name);
    setEvent((prev) => prev ? { ...prev, participants: [...prev.participants, p] } : prev);
    return p;
  };

  const createExpense = async (input: CreateExpenseInput): Promise<Expense> => {
    const exp = await services.api.createExpense(input);
    setEvent((prev) => prev ? { ...prev, expenses: [exp, ...prev.expenses] } : prev);
    return exp;
  };

  const updateExpense = async (id: string, input: Partial<CreateExpenseInput>): Promise<Expense> => {
    const exp = await services.api.updateExpense(id, input);
    setEvent((prev) => prev ? {
      ...prev,
      expenses: prev.expenses.map((e) => (e.id === id ? exp : e)),
    } : prev);
    return exp;
  };

  const deleteExpense = async (id: string): Promise<void> => {
    if (!event || !activeParticipant) return;
    await services.api.deleteExpense(event.id, id, activeParticipant.id);
    setEvent((prev) => prev ? {
      ...prev,
      expenses: prev.expenses.filter((e) => e.id !== id),
    } : prev);
  };

  const createSettlement = async (input: CreateSettlementInput): Promise<Settlement> => {
    const set = await services.api.createSettlement(input);
    setEvent((prev) => prev ? {
      ...prev,
      settlements: [set, ...prev.settlements],
    } : prev);
    return set;
  };

  return (
    <EventContext.Provider
      value={{
        event,
        activeParticipant,
        onlineParticipantIds,
        isLoading,
        error,
        isMock: services.isMock,
        setActiveParticipant,
        loadEvent,
        createEvent,
        addParticipant,
        createExpense,
        updateExpense,
        deleteExpense,
        createSettlement,
        lastUpdatedItemId,
      }}
    >
      {children}
    </EventContext.Provider>
  );
};

export const useEvent = () => {
  const ctx = useContext(EventContext);
  if (!ctx) throw new Error('useEvent must be used within an EventProvider');
  return ctx;
};
