# ADR 001: Technology Stack Selection for Household Chore Manager (Web-First MVP)

* **Status:** Accepted
* **Date:** 2026-09-04
* **Deciders:** Engineering Team & Product Owner
* **Consulted:** Architecture Review

---

## Context and Problem Statement

The **Household Chore Manager** is a collaborative task management application designed for shared apartments. 
The immediate goal is to establish a streamlined, robust **Web-First MVP** that solves household chore coordination without introducing unnecessary operational overhead.

Key requirements for the MVP:
1. A rich, responsive web interface for managing chore templates, reviewing leaderboard statistics, claiming tasks, and tracking deadlines.
2. Automated chore rotation (Round-Robin) and recurring chore generation (Daily, Weekly, Bi-weekly, Monthly).
3. In-app visual deadline tracking (Due Soon, Overdue indicators).
4. Fast time-to-market with a clean, maintainable architecture using a single language (Python) and zero complex frontend build pipelines.

*Note on Telegram Bot:* External messaging integrations (Telegram Bot) are explicitly deferred from the initial MVP to keep the architecture focused and reduce deployment/testing complexity. The backend design will retain modular service layers so a Telegram bot or mobile client can be added seamlessly in a subsequent release.

---

## Decision Drivers

* **Rapid MVP Delivery:** Leverage built-in capabilities (authentication, database management, admin console) rather than developing boilerplate from scratch.
* **Low Operational Overhead:** Ability to run with zero external services (SQLite locally, portable to PostgreSQL; no Redis/Celery/message brokers needed).
* **Modern, Dynamic UX without Heavy Toolchains:** Deliver responsive single-page application (SPA) dynamics using HTMX and Vanilla CSS without Node.js, npm, or complex frontend bundlers.
* **Cohesive Python Architecture:** Single language and runtime across backend, business services, and task scheduling.
* **Clean Extensibility:** Business logic encapsulated in reusable services (`rotation_service.py`, `scheduler.py`) to allow future notification channels (Telegram, Email, WebPush) to be plugged in effortlessly.

---

## Considered Options

### Option 1: Django 5.x + HTMX + APScheduler (Selected)
* **Backend:** Django 5.x (Python 3.11+)
* **Frontend:** Django Templates + HTMX + Modern Vanilla CSS
* **Database:** SQLite (local development) / PostgreSQL (production)
* **Background Scheduler:** In-process APScheduler (background thread for recurring chore generation & status transitions)
* **External Integrations:** None in MVP (Deferred to Phase 2)

### Option 2: Asynchronous Python (FastAPI + SQLModel/SQLAlchemy)
* **Backend:** FastAPI (ASGI)
* **Frontend:** Jinja2 + HTMX or React SPA (Vite)
* **Database:** SQLite / PostgreSQL + SQLAlchemy
* **Scheduler:** AsyncIOScheduler / ARQ

### Option 3: Full-Stack TypeScript (Next.js + Prisma)
* **Backend & Frontend:** Next.js (App Router, Server Actions)
* **ORM & Database:** Prisma / PostgreSQL
* **Scheduler:** Node-cron

### Option 4: Lightweight Python Microframework (Flask + Peewee)
* **Backend:** Flask
* **Database:** Peewee + SQLite
* **Scheduler:** `schedule` library

---

## Decision Outcome

**Chosen Option:** **Option 1: Django 5.x + HTMX + APScheduler (Web-First)**

### Rationale:
1. **Batteries-Included Acceleration:** Django provides battle-tested user authentication, CSRF security, session handling, and an out-of-the-box **Django Admin** interface. The admin panel eliminates the need to manually build CRUD interfaces for managing chore templates, system logs, and user profiles during early testing.
2. **Dynamic UI with Zero Frontend Toolchain:** HTMX enables seamless DOM swaps, asynchronous actions (instant chore claiming and status changes), and modal workflows directly within HTML attributes. No Node.js, npm dependencies, or build steps are introduced into the repository.
3. **Focused MVP Scope (No Telegram Overhead):** Excluding external bot polling eliminates long-polling workers, public webhook/tunnel configurations (e.g. ngrok), and multi-platform state sync from the critical path.
4. **Service-Layer Architecture:** Pure domain logic lives in `chores/services/rotation_service.py` and `chores/services/scheduler.py`, completely decoupled from presentation views.

---

## Pros and Cons of the Chosen Option

### Positive Consequences
* **Extreme Simplicity & Speed:** Standard `pip install -r requirements.txt` (`Django`, `apscheduler`, `python-dotenv`) is all that is required to run the full application.
* **Instant Admin Control:** Full visibility and manipulation of database models through Django Admin.
* **Single Web Process:** Both the HTTP server and the light background scheduler can run together smoothly during development.
* **Future-Proof:** Future addition of Telegram or mobile APIs simply consumes the existing `services/` layer without refactoring the domain core.

### Negative Consequences & Mitigations
* **Scheduler Multi-Worker Duplication:** Running APScheduler directly inside WSGI processes can cause duplicate task execution when scaled across multiple web workers.
  * *Mitigation:* For production, run the scheduler via a dedicated management command (`python manage.py process_tasks`) or configure a mutex/lock table in the database.
* **Real-Time Multi-User Updates:** Multiple roommates looking at the board simultaneously do not get automatic WebSocket pushes without page refresh or polling.
  * *Mitigation:* Leverage lightweight HTMX polling triggers (e.g., `hx-trigger="every 15s"` on the board container) for near-real-time updates without WebSockets complexity.

---

## References
* Master Plan: `_docs/plan.md`
