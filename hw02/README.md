# Tavli ⚡

> Zero-friction, mobile-first Progressive Web Application (PWA) for collaborative expense tracking, dish-by-dish itemized bill breakdowns, and debt settlement without account registration.

---

## 🌟 Features

- **Zero Friction Onboarding:** Share unique link or QR code — no accounts or passwords required. Claim your identity on first visit.
- **Hybrid Splitting:**
  - **Quick Split:** Equal, exact amounts, or custom shares/weights.
  - **Itemized / Receipt Mode:** Dish-by-dish item allocation with automatic **proportional distribution of tax & tip**.
- **Live Multi-Currency:** Dynamic conversion powered by European Central Bank (ECB) reference rates with instant live preview.
- **Dual Debt Settlement Engine:**
  - **Simplified (Default):** Minimizes total transaction count using greedy flow heuristic.
  - **Direct / Pairwise:** Preserves bilateral historical links.
  - **1-Tap Settle Up:** Fast debt recording with instant balance recalculation.
- **Real-Time Collaboration & Audit Trail:** WebSocket synchronization with presence avatars and an append-only activity feed with diffs.
- **Centralized Service Architecture:** Runs 100% standalone out of the box with an in-memory & `localStorage` mock backend, ready to seamlessly plug into real backend endpoints.

---

## 🚀 Quick Start

### Using Make (Recommended)

Run everything from the project root using the unified [Makefile](file:///Users/user/Documents/Python/ai-dev-tools-zoomcamp-2026-hw02/Makefile):

```bash
# Install dependencies for both backend and frontend
make install

# Run full checks (backend pytest, frontend tests, linting, and build)
make check

# Run backend & frontend concurrently in development mode
make dev

# Or run tests specifically
make test
```

---

### 1. Frontend (Standalone with Mock Backend)

The frontend is built with React, TypeScript, and Vite, and includes a full mock service layer so you can run it immediately without starting the backend.

```bash
cd frontend

# Install dependencies
npm install

# Start local development server
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

#### Running Tests & Build:

```bash
# Run unit & integration test suite (Vitest)
npm test

# Run build & TypeScript check
npm run build
```

---

### 2. Backend (Upcoming / Under Development)

The backend uses Python with `uv` for dependency management:

```bash
cd backend

# Sync dependencies
uv sync

# Add dependency
uv add <PACKAGE-NAME>

# Run script
uv run python <PYTHON-FILE>
```

---

## ⚙️ Environment Configuration

When switching the frontend from the mock service layer to a real backend API:

Create `frontend/.env.local`:
```ini
# Toggle mock service (default is true)
VITE_USE_MOCK=false

# Real API and WebSocket base URLs
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

---

## 📚 Documentation

- [Product & Technical Specifications](_docs/specs.md): Architecture, data schema, WebSocket protocol, and debt resolution algorithms.
- [Frontend Specifications](_docs/frontend_specs.md): User journeys, screen states, component tree, and UX decisions.
- [Agent Instructions](AGENTS.md): Guidelines and commands for AI agents and developers.
