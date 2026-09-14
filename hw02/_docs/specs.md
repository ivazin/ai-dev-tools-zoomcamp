# Product & Technical Specification: Expense Splitter (MVP)

## 1. Executive Summary

A zero-friction, mobile-first Progressive Web Application (PWA) designed for trip groups, one-off events, and shared dinners. The app enables real-time collaborative expense tracking and debt settlement without requiring account registration.

### Key Value Propositions

* **Zero Onboarding Friction:** Instant event creation via unique shareable URL/QR code.
* **Hybrid Expense Tracking:** Fast total-amount splitting alongside dish-by-dish itemized bill breakdowns (with proportional tax/tip).
* **Live Multi-Currency:** Real-time exchange rate normalization powered by the European Central Bank (ECB) Data Portal API.
* **Dual Settlement Engine:** Minimized transaction routing (default) with a toggleable pairwise/direct debt ledger.
* **Real-Time Collaboration & Auditing:** WebSocket-driven live updates with an append-only activity log for every mutation.

---

## 2. Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (PWA / Mobile Web)                │
│  - Offline Service Worker   - LocalStorage Session / Cache  │
│  - Real-Time WS Listener    - Responsive Touch UI           │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / WSS
┌──────────────────────────────▼──────────────────────────────┐
│                    Application Backend                      │
│  - REST API (CRUD)          - WebSocket Engine (Pub/Sub)    │
│  - Debt Graph Resolver      - ECB Rate Sync Worker          │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                   Relational Persistence                    │
│  - Events & Participants    - Expenses & Itemized Splits    │
│  - Audit / Activity Log     - Exchange Rate Cache           │
└─────────────────────────────────────────────────────────────┘

```

* **Frontend:** Mobile-first PWA (React / Svelte / Vue), Tailwind CSS, Service Workers for asset caching.
* **Backend:** Node.js (Fastify/Express) or Python (FastAPI) or Go.
* **Real-Time Layer:** WebSockets (`ws` / Socket.io) for bidirectional sync and active participant presence.
* **Database:** Relational schema (PostgreSQL or SQLite/LibSQL) ensuring ACID transactions on monetary operations.
* **External Integrations:** European Central Bank (ECB) daily reference rates feed (`eurofxref-daily.xml` or JSON API).

---

## 3. Access Model & Security

### Capability-Based URLs

* Events are secured via high-entropy, URL-safe identifiers (21-character NanoID / UUIDv4):
`[https://split.domain.app/e/v1StGXR8_Z5jdHi6B-myT](https://split.domain.app/e/v1StGXR8_Z5jdHi6B-myT)`
* Anyone holding the link has full read and write permissions to the event.

### Identity & Sessions

* **No Passwords / No Auth:** Users choose or claim a participant name on their first visit.
* **Device Session:** Participant ID is saved to `localStorage`. Reopening the link automatically reconnects the user to that identity.
* **Impersonation Safeguard:** A user can switch active profiles only within the event's defined participant list, and all changes are attributed to the active participant in the activity log.

---

## 4. Functional Requirements

### 4.1 Event Management

* **Create Event:** Name/title, default base currency (e.g., EUR, USD), and initial participant names.
* **Share Event:** Copyable shortlink and native QR code generator for in-person scanning.
* **Participant Roster:** Add new participants at any time. Participants with logged transactions cannot be deleted (only deactivated/hidden).

### 4.2 Hybrid Expense Logging

```
                          ┌──────────────────────────┐
                          │     Create Expense       │
                          └─────────────┬────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │   Total-Amount Split  │               │     Itemized Bill     │
        │  (Payer -> Debtors)   │               │   (Line-item level)   │
        └───────────┬───────────┘               └───────────┬───────────┘
                    │                                       │
      ┌─────────────┼─────────────┐                         ▼
      ▼             ▼             ▼             * Name & price per item
    Equal      Exact Shares   Percentages       * Assign diners per item
                                                * Proportional Tax & Tip

```

* **Common Fields:** Description, total amount, original currency, payer, date/time.
* **Mode A: Total-Amount Split:**
* *Equal:* Divided evenly among selected participants.
* *Exact / Unequal amounts:* Specific numeric amount per debtor.
* *Percentages / Shares:* Weight-based distribution (e.g., 2 shares vs. 1 share).


* **Mode B: Itemized Breakdown (Dinner / Receipt mode):**
* Enter individual items (e.g., "Burger €15", "Wine €30").
* Assign 1 to $N$ consumers per line item (split evenly among assignees).
* Global Tax, Tip, and Service Charge inputs, calculated **proportionally** according to each participant's subtotal share.



### 4.3 Multi-Currency & ECB Integration

* **Base Currency:** Each event has one designated settlement currency.
* **Exchange Rate Pipeline:**
1. Backend fetches ECB daily reference rates every 24 hours.
2. Expenses recorded in non-base currencies fetch the ECB spot rate corresponding to the expense date (fallback: latest available).
3. The record stores: `original_amount`, `original_currency`, `exchange_rate_to_base`, and `base_amount`.


* **Settlement Guarantee:** All debt graphs are calculated strictly using the converted `base_amount` to prevent currency drift.

### 4.4 Debt Settlement Engine

| Feature | Simplified Debts (Default) | Direct / Pairwise Debts |
| --- | --- | --- |
| **Objective** | Minimize transaction count. | Maintain exact historical debtor-to-creditor links. |
| **Algorithm** | Net balance reduction (Greedy / Flow). | Direct bilateral netting between pairs. |
| **Output Example** | Alice pays Charlie €20. | Alice pays Bob €20; Bob pays Charlie €20. |
| **Best For** | Group trips, vacations, house shares. | People who don't know each other well. |

* **Settle Up Action:** Users can log a settlement (Payer $\to$ Payee $\to$ Amount). Settlements appear as transactions and deduct from outstanding balances.

### 4.5 Activity Log & Audit Trail

* Every write mutation (insert, update, delete, settlement) writes an immutable record to the `activity_log` table:
* `timestamp`, `actor_participant_id`, `action_type`, `entity_id`, `change_diff` (JSON).


* Frontend exposes an "Activity Feed" panel showing real-time chronological actions:
> *"Max edited 'Dinner' (changed total from €80 to €92) — 2 mins ago"*



---

## 5. Data Schema

```sql
CREATE TABLE events (
    id VARCHAR(32) PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    base_currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(32) REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(80) NOT NULL,
    avatar_color VARCHAR(7),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(32) REFERENCES events(id) ON DELETE CASCADE,
    payer_id UUID REFERENCES participants(id),
    description VARCHAR(255) NOT NULL,
    original_amount DECIMAL(12, 2) NOT NULL,
    original_currency VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(12, 6) NOT NULL DEFAULT 1.000000,
    base_amount DECIMAL(12, 2) NOT NULL,
    is_itemized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expense_splits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id UUID REFERENCES expenses(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id),
    computed_base_amount DECIMAL(12, 2) NOT NULL
);

CREATE TABLE line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id UUID REFERENCES expenses(id) ON DELETE CASCADE,
    title VARCHAR(120) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL
);

CREATE TABLE line_item_consumers (
    line_item_id UUID REFERENCES line_items(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id),
    PRIMARY KEY (line_item_id, participant_id)
);

CREATE TABLE settlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(32) REFERENCES events(id) ON DELETE CASCADE,
    from_participant_id UUID REFERENCES participants(id),
    to_participant_id UUID REFERENCES participants(id),
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activity_log (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(32) REFERENCES events(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES participants(id),
    action VARCHAR(50) NOT NULL,
    details JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exchange_rates (
    currency VARCHAR(3) NOT NULL,
    rate_date DATE NOT NULL,
    rate_to_eur DECIMAL(12, 6) NOT NULL,
    PRIMARY KEY (currency, rate_date)
);

```

---

## 6. Real-Time WebSocket Protocol

### Connection Lifecycle

1. Client establishes connection: `wss://split.domain.app/ws/events/{eventId}`.
2. Client sends join message with participant ID:
```json
{ "type": "JOIN", "participantId": "uuid-1234" }

```


3. Server tracks presence and responds with active client list.

### Broadcast Events

When any participant modifies state, server publishes to the event channel:

```json
{
  "type": "EXPENSE_CREATED",
  "actorId": "uuid-1234",
  "timestamp": "2026-09-14T08:30:00Z",
  "payload": {
    "expenseId": "uuid-5678",
    "description": "Team Tapas",
    "baseAmount": 84.50,
    "payerId": "uuid-1234"
  }
}

```

*Supported Event Types:* `PARTICIPANT_ADDED`, `EXPENSE_CREATED`, `EXPENSE_UPDATED`, `EXPENSE_DELETED`, `SETTLEMENT_RECORDED`, `RATES_UPDATED`.

---

## 7. Debt Resolution Algorithms

### 7.1 Net Balance Calculation

For every participant $p$:


$$\text{Balance}(p) = \sum \text{PaidAsPayer}(p) + \sum \text{ReceivedInSettlement}(p) - \sum \text{OwedAsDebtor}(p) - \sum \text{PaidInSettlement}(p)$$

### 7.2 Simplified Debt Minimization (Greedy Heuristic)

1. Compute $\text{Balance}(p)$ for all participants.
2. Separate into two lists:
* **Debtors:** Balance $< 0$ (sorted ascending by amount owed).
* **Creditors:** Balance $> 0$ (sorted descending by amount to receive).


3. Match the largest debtor with the largest creditor:

$$\text{Transfer} = \min(\vert{}\text{DebtorBalance}\vert{}, \text{CreditorBalance})$$


4. Record transfer, adjust balances, and repeat until all balances reach 0.

### 7.3 Direct / Pairwise Calculation

Maintain a directed matrix $M[i][j]$ representing direct debts accrued from individual shared expenses minus direct settlements, without transitive transfers.

---

## 8. MVP Development Milestones

* **Milestone 1: Core Engine & Data Model**
* SQLite/PostgreSQL schema setup.
* REST endpoints for event creation, participants, and manual expense creation.
* Unit tests for debt simplification and itemized split math.


* **Milestone 2: ECB Currency Ingestion**
* Cron/Worker integration with ECB Data Portal feed.
* Multi-currency conversion pipeline on expense submission.


* **Milestone 3: Mobile PWA & UI Flow**
* Mobile-first responsive screens: Event Dashboard, Add Expense (Tabs: Simple vs. Itemized), Balance/Settlement tab.
* LocalStorage participant persistence.


* **Milestone 4: WebSockets & Audit Ledger**
* Live channel broadcasting and optimistic UI updates.
* Activity feed interface showing real-time event logs.