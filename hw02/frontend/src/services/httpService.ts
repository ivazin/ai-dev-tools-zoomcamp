import {
  CurrencyCode,
  EventData,
  CreateEventInput,
  CreateExpenseInput,
  Expense,
  CreateSettlementInput,
  Settlement,
  Participant,
} from '../types';
import {
  IApiService,
  IRealtimeService,
  RealtimeSubscriber,
  RealtimeMessage,
} from '../types/services';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}/ws`;

export class HttpApiService implements IApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.message || `HTTP ${res.status}: ${res.statusText}`);
    }

    return res.json();
  }

  async getEvent(eventId: string): Promise<EventData> {
    return this.request<EventData>(`/events/${eventId}`);
  }

  async createEvent(input: CreateEventInput): Promise<EventData> {
    return this.request<EventData>('/events', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async addParticipant(eventId: string, name: string): Promise<Participant> {
    return this.request<Participant>(`/events/${eventId}/participants`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async createExpense(input: CreateExpenseInput): Promise<Expense> {
    return this.request<Expense>(`/events/${input.eventId}/expenses`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async updateExpense(expenseId: string, input: Partial<CreateExpenseInput>): Promise<Expense> {
    return this.request<Expense>(`/expenses/${expenseId}`, {
      method: 'PUT',
      body: JSON.stringify(input),
    });
  }

  async deleteExpense(eventId: string, expenseId: string, actorId: string): Promise<void> {
    await this.request<void>(`/events/${eventId}/expenses/${expenseId}`, {
      method: 'DELETE',
      body: JSON.stringify({ actorId }),
    });
  }

  async createSettlement(input: CreateSettlementInput): Promise<Settlement> {
    return this.request<Settlement>(`/events/${input.eventId}/settlements`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async getExchangeRate(
    fromCurrency: CurrencyCode,
    toCurrency: CurrencyCode,
    date?: string
  ): Promise<{ rate: number; date: string }> {
    const params = new URLSearchParams({ from: fromCurrency, to: toCurrency });
    if (date) params.append('date', date);
    return this.request<{ rate: number; date: string }>(`/exchange-rates?${params.toString()}`);
  }
}

export class WebSocketRealtimeService implements IRealtimeService {
  private socket: WebSocket | null = null;
  private subscribers = new Set<RealtimeSubscriber>();
  private onlineUsers: string[] = [];

  connect(eventId: string, participantId: string): void {
    if (this.socket) {
      this.socket.close();
    }

    try {
      this.socket = new WebSocket(`${WS_BASE_URL}/events/${eventId}`);

      this.socket.onopen = () => {
        this.socket?.send(JSON.stringify({ type: 'JOIN', participantId }));
      };

      this.socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as RealtimeMessage;
          if (msg.type === 'PRESENCE_CHANGE' && (msg.payload as { onlineParticipants?: string[] })?.onlineParticipants) {
            this.onlineUsers = (msg.payload as { onlineParticipants: string[] }).onlineParticipants;
          }
          this.subscribers.forEach((sub) => sub(msg));
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.socket.onclose = () => {
        // Simple reconnect after 3 seconds
        setTimeout(() => {
          if (this.socket?.readyState === WebSocket.CLOSED) {
            this.connect(eventId, participantId);
          }
        }, 3000);
      };
    } catch (err) {
      console.warn('Real WebSocket connection failed, check backend availability:', err);
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.subscribers.clear();
  }

  subscribe(callback: RealtimeSubscriber): () => void {
    this.subscribers.add(callback);
    return () => {
      this.subscribers.delete(callback);
    };
  }

  getOnlineParticipants(): string[] {
    return this.onlineUsers;
  }
}

export const httpApiService = new HttpApiService();
export const webSocketRealtimeService = new WebSocketRealtimeService();
