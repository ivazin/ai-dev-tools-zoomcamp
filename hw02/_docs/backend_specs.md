# Backend Technical Specification: SplitWave API & Real-Time Service

## 1. Executive Summary & Architecture Overview

The SplitWave backend provides the RESTful persistence and real-time collaboration engine for the SplitWave expense splitting application. It is designed to be lightweight, fully asynchronous, stateless, and cloud-native (Kubernetes-ready).

### Core Stack
* **Language & Runtime:** Python 3.12+ managed via `uv`.
* **Web Framework:** FastAPI (ASGI via Uvicorn).
* **Validation & Schemas:** Pydantic v2 (aligned 1:1 with `openapi.yaml`).
* **ORM & Database Abstraction:** SQLAlchemy 2.0 (asyncio) with Alembic for migrations.
* **Storage Engines:**
  * Development / Test: SQLite (`sqlite+aiosqlite:///...`)
  * Production / Staging: PostgreSQL 16+ (`postgresql+asyncpg://...`)
* **Real-Time Pub/Sub & WebSockets:** FastAPI WebSocket endpoints backed by an abstract broadcast layer (`InMemory` for local dev/testing, `Redis` for multi-replica production).
* **Background Processing:** External currency rate ingestion (European Central Bank - ECB Data Portal) scheduled via async worker or Kubernetes CronJob.

---

## 2. Kubernetes & Scalability Architecture

```
                          ┌───────────────────────────┐
                          │     Ingress Controller    │
                          │   (Nginx / Traefik / AWS) │
                          └─────────────┬─────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     │ (HTTP REST / WebSocket Handshake)   │
                     ▼                                     ▼
          ┌─────────────────────┐               ┌─────────────────────┐
          │    FastAPI Pod 1    │               │    FastAPI Pod N    │
          │  (Uvicorn worker)   │               │  (Uvicorn worker)   │
          └──────┬───────┬──────┘               └──────┬───────┬──────┘
                 │       │                             │       │
                 │       └──────────────┬──────────────┘       │
                 │                      │                      │
          SQL Connection Pool           │ Redis Pub/Sub        │
                 │                      ▼                      │
                 │          ┌───────────────────────┐          │
                 │          │     Redis Cluster     │          │
                 │          │  (Event Room Pub/Sub) │          │
                 │          └───────────────────────┘          │
                 ▼                                             ▼
          ┌───────────────────────────────────────────────────────────┐
          │             PostgreSQL Primary + Read Replicas            │
          │               (PgBouncer Connection Pooling)              │
          └───────────────────────────────────────────────────────────┘
```

### 2.1 Stateless Design
* **Capability-Based Access:** All resources are keyed by high-entropy event identifiers (`eventId`). There are no sticky server-side sessions or local filesystem state.
* **Horizontal Pod Autoscaling (HPA):** Pods can scale dynamically based on CPU, memory, or active WebSocket connection counts.

### 2.2 Multi-Pod Real-Time Sync (Redis Pub/Sub)
* When a write mutation (expense creation, update, deletion, settlement) occurs on `Pod A`:
  1. The transaction is committed to PostgreSQL.
  2. `Pod A` publishes an event envelope to Redis: channel `splitwave:events:{eventId}`.
  3. All pods (`Pod A`, `Pod B`, ..., `Pod N`) listening to that Redis channel broadcast the message to their local active WebSocket connections in that event room.
* **Local Fallback:** In local development mode (`REDIS_URL` empty), an in-memory dictionary-based broadcaster is used automatically.

### 2.3 Database Connection Management
* Asynchronous connection pooling via `asyncpg`.
* Pool parameters configured via environment variables:
  * `DB_POOL_SIZE` (default: 10)
  * `DB_MAX_OVERFLOW` (default: 20)
  * `DB_POOL_TIMEOUT` (default: 30)
* In Kubernetes with high replica counts, external connection pooling (such as PgBouncer or Cloud SQL / RDS Proxy) is utilized to avoid saturating PostgreSQL process limits.

---

## 3. Data Schema & Persistence

All monetary values are stored as exact decimal numbers (`DECIMAL(12, 2)` or `NUMERIC(12, 2)`) to avoid floating-point inaccuracies. Currency exchange rates use `DECIMAL(12, 6)`.

```
 events
 ├── id (VARCHAR(32), PK, NanoID/UUID)
 ├── title (VARCHAR(120))
 ├── base_currency (VARCHAR(3))
 └── created_at (TIMESTAMPTZ)

 participants
 ├── id (UUID, PK)
 ├── event_id (FK -> events.id ON DELETE CASCADE)
 ├── name (VARCHAR(80))
 ├── avatar_color (VARCHAR(7))
 └── created_at (TIMESTAMPTZ)

 expenses
 ├── id (UUID, PK)
 ├── event_id (FK -> events.id ON DELETE CASCADE)
 ├── payer_id (FK -> participants.id)
 ├── description (VARCHAR(255))
 ├── original_amount (DECIMAL(12,2))
 ├── original_currency (VARCHAR(3))
 ├── exchange_rate (DECIMAL(12,6))
 ├── base_amount (DECIMAL(12,2))
 ├── is_itemized (BOOLEAN)
 ├── created_at (TIMESTAMPTZ)
 └── updated_at (TIMESTAMPTZ)

 expense_splits
 ├── id (UUID, PK)
 ├── expense_id (FK -> expenses.id ON DELETE CASCADE)
 ├── participant_id (FK -> participants.id)
 └── computed_base_amount (DECIMAL(12,2))

 line_items
 ├── id (UUID, PK)
 ├── expense_id (FK -> expenses.id ON DELETE CASCADE)
 ├── title (VARCHAR(120))
 └── amount (DECIMAL(12,2))

 line_item_consumers
 ├── line_item_id (FK -> line_items.id ON DELETE CASCADE)
 └── participant_id (FK -> participants.id)
 (PK: line_item_id, participant_id)

 settlements
 ├── id (UUID, PK)
 ├── event_id (FK -> events.id ON DELETE CASCADE)
 ├── from_participant_id (FK -> participants.id)
 ├── to_participant_id (FK -> participants.id)
 ├── amount (DECIMAL(12,2))
 ├── currency (VARCHAR(3))
 └── created_at (TIMESTAMPTZ)

 activity_log
 ├── id (BIGSERIAL/INTEGER, PK)
 ├── event_id (FK -> events.id ON DELETE CASCADE)
 ├── actor_id (FK -> participants.id)
 ├── action (VARCHAR(50))
 ├── details (JSON / JSONB)
 └── created_at (TIMESTAMPTZ)

 exchange_rates
 ├── currency (VARCHAR(3))
 ├── rate_date (DATE)
 ├── rate_to_eur (DECIMAL(12,6))
 └── PK: (currency, rate_date)
```

---

## 4. API Endpoints & Contract Conformance

The REST API strictly implements the contract specified in `openapi.yaml`.

### 4.1 Event Lifecycle (`/api/events`)
* `POST /api/events`: Create new event with initial participants and base currency.
* `GET /api/events/{eventId}`: Fetch full event aggregate (event details, participants, expenses, splits, settlements).
* `POST /api/events/{eventId}/participants`: Add a participant to an existing event.
* `PATCH /api/events/{eventId}/participants/{participantId}`: Update participant profile (name, avatar color).

### 4.2 Expenses & Splits (`/api/events/{eventId}/expenses`)
* `POST /api/events/{eventId}/expenses`: Create expense (supports both Total-Amount split models and Itemized breakdowns).
* `PUT /api/events/{eventId}/expenses/{expenseId}`: Full update of an expense.
* `DELETE /api/events/{eventId}/expenses/{expenseId}`: Delete expense and cascade-remove splits.

### 4.3 Settlements (`/api/events/{eventId}/settlements`)
* `POST /api/events/{eventId}/settlements`: Record a direct payment between two participants.
* `DELETE /api/events/{eventId}/settlements/{settlementId}`: Revert a settlement payment.

### 4.4 Exchange Rates (`/api/rates`)
* `GET /api/rates/latest`: Returns current cached reference rates.
* `GET /api/rates/convert`: Convert amount between two currencies based on ECB rates.

### 4.5 Health & Probes
* `GET /api/health/live`: Liveness probe (checks event loop responsiveness).
* `GET /api/health/ready`: Readiness probe (validates database pool and Redis connection).

---

## 5. WebSocket Real-Time Protocol

### 5.1 Endpoint & Authentication
* **URL:** `/ws/events/{eventId}`
* **Connection Handshake:**
  1. Client connects via WebSocket.
  2. Client immediately sends a `JOIN` frame:
     ```json
     { "type": "JOIN", "participantId": "uuid-1234" }
     ```
  3. Server acknowledges with `ROOM_JOINED` including active participants present.

### 5.2 Server-to-Client Broadcast Events
Whenever a state mutation succeeds, the server broadcasts an event payload to all clients in the event room:
* `PARTICIPANT_ADDED`: New participant joined the roster.
* `PARTICIPANT_UPDATED`: Participant name or color changed.
* `EXPENSE_CREATED`: New expense logged.
* `EXPENSE_UPDATED`: Expense modified.
* `EXPENSE_DELETED`: Expense removed.
* `SETTLEMENT_RECORDED`: Debt settlement logged.
* `SETTLEMENT_DELETED`: Settlement removed.
* `PRESENCE_UPDATED`: Client presence (online/offline) state changes.

---

## 6. Currency Ingestion & Settlement Engine

### 6.1 ECB Exchange Rate Ingestion
* **Source:** European Central Bank official daily reference feed:
  `https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`
* **Schedule:** Daily at 16:30 CET.
* **Execution Options:**
  1. Local/Single Pod: Integrated asynchronous background task (`apscheduler` or `asyncio`).
  2. Kubernetes Production: Dedicated Kubernetes `CronJob` running `uv run python -m app.workers.ecb_sync`.

### 6.2 Debt Minimization (Greedy Algorithm)
1. Compute net balance $B(p)$ for each participant $p$:
   $$B(p) = \text{TotalPaid}(p) + \text{ReceivedSettlements}(p) - \text{TotalOwed}(p) - \text{PaidSettlements}(p)$$
2. Classify participants into Creditors ($B > 0$) and Debtors ($B < 0$).
3. Greedily pair the maximal debtor with the maximal creditor until all balances are resolved to 0.00.

---

## 7. Project Structure & Dependency Management

Dependencies are strictly managed via `uv` as defined in `AGENTS.md`.

```
backend/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py                 # FastAPI application factory & routes registration
│   ├── config.py               # Pydantic-settings environment configuration
│   ├── database.py             # Async SQLAlchemy engine & session factory
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── event.py
│   │   ├── participant.py
│   │   ├── expense.py
│   │   ├── settlement.py
│   │   ├── activity.py
│   │   └── rate.py
│   ├── schemas/                # Pydantic v2 validation DTOs matching openapi.yaml
│   ├── routers/                # FastAPI endpoint handlers
│   │   ├── events.py
│   │   ├── expenses.py
│   │   ├── settlements.py
│   │   ├── rates.py
│   │   ├── websockets.py
│   │   └── health.py
│   ├── services/               # Core business logic
│   │   ├── debt_engine.py      # Greedy debt minimization math
│   │   ├── split_calculator.py # Itemized & proportional bill calculations
│   │   ├── ecb_service.py      # ECB currency ingestion & conversion
│   │   └── broadcaster.py      # Abstract Pub/Sub (InMemory & Redis implementations)
│   └── workers/
│       └── ecb_sync.py         # Standalone sync task for CronJob execution
└── tests/
    ├── test_api_events.py
    ├── test_debt_engine.py
    ├── test_split_calculator.py
    └── test_websockets.py
```

### Essential uv Commands
```bash
# Initialize & sync dependencies
uv sync

# Add dependencies
uv add fastapi uvicorn sqlalchemy alembic asyncpg aiosqlite pydantic pydantic-settings httpx redis

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run migrations
uv run alembic upgrade head

# Run tests
uv run pytest
```
