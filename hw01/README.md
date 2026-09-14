# Household Chore Manager

Collaborative task management application designed for shared apartments and households.

---

## Features Implemented (Phase 1 & 2)

- **Domain Models & Migrations (`chores/models.py`)**:
  - `UserProfile`: Extends Django's `User` with `total_points` and `is_active_roommate`.
  - `ChoreTemplate`: Templates with recurrence frequencies (`DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`) and strategies (`ROUND_ROBIN`, `CLAIM_POOL`, `FIXED`).
  - `Chore`: Individual chores with statuses (`PENDING`, `CLAIMABLE`, `COMPLETED`, `OVERDUE`), deadlines, and points.
  - `ChoreLog`: Audit history for tracking actions (`CREATED`, `CLAIMED`, `COMPLETED`, `REASSIGNED`, `OVERDUE_ALERT`).
- **Django Admin Interface (`chores/admin.py`)**:
  - Comprehensive model administration with filters, searches, and inlined `ChoreLog` history records.
- **Round-Robin Rotation Service (`chores/services/rotation_service.py`)**:
  - Deterministic rotation progression, circular cycling, handling inactive users and non-existent IDs.
- **Chore Lifecycle Service (`chores/services/chore_service.py`)**:
  - Domain service for claiming open chores, atomic completion with point awards, reassignment, and automatic rotation triggers.
- **Seed Data Command (`python manage.py seed_data`)**:
  - Populates a realistic development household with admin account, roommates, templates, active chores across all lifecycle states, and logs.

---

## Quickstart Guide

### 1. Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Setup & Installation

Clone repository and install dependencies:

```bash
uv sync
```

Set up local environment file:

```bash
cp .env.example .env
```

Apply database migrations:

```bash
uv run python manage.py migrate
```

Populate the database with sample data:

```bash
uv run python manage.py seed_data
```

*(Use `--clean` flag to wipe sample chore data and re-seed from scratch: `uv run python manage.py seed_data --clean`)*

### 3. Run Development Server

```bash
uv run python manage.py runserver
```

Open your browser at **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**

#### Default Seeded Credentials

- **Admin Superuser**:
  - Username: `admin`
  - Password: `adminpassword`
- **Roommates**:
  - Usernames: `alice` (25 pts), `bob` (15 pts), `charlie` (10 pts), `dana` (0 pts)
  - Password: `password123`

---

## Testing

Run the full automated test suite (67 tests across models, admin, services, and commands):

```bash
uv run pytest
```

Run specific test modules:

```bash
# Model unit tests
uv run pytest tests/test_models.py

# Rotation domain service tests
uv run pytest tests/test_rotation.py

# Chore lifecycle & points service tests
uv run pytest tests/test_chore_service.py

# Admin views & permissions tests
uv run pytest tests/test_admin.py

# Management command tests
uv run pytest tests/test_commands.py
```

Run test suite with coverage:

```bash
uv run pytest --cov=chores
```

---

## Documentation

- [`_docs/plan.md`](_docs/plan.md): Full technical specification, architectural decisions, and project implementation roadmap.
- [`_docs/process.md`](_docs/process.md): Autonomous agent workflow and subagent lifecycle roles (PM $\rightarrow$ Engineer $\rightarrow$ QA).
- [`_docs/design-system.md`](_docs/design-system.md): Frontend CSS design tokens, typography, and styling guidelines.
- [`_docs/testing-guidelines.md`](_docs/testing-guidelines.md): Testing conventions and pytest standards.
- [`_docs/adr-001-tech-stack.md`](_docs/adr-001-tech-stack.md): Architecture Decision Record for backend framework and frontend architecture.
