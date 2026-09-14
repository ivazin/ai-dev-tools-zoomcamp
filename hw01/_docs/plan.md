# Project Specification & Implementation Plan: Household Chore Manager

## 1. Executive Summary
The **Household Chore Manager** is a full-featured, collaborative task management system designed specifically for shared apartments and households. It provides an interactive, modern web dashboard to keep housemates aligned, distribute chores equitably, track points/leaderboards, and eliminate chore-related friction.

*Scope Note:* The project follows a **Web-First MVP** approach. External messaging integrations (such as a Telegram Bot) are designed into the service layer but deferred to a future phase, allowing the core application, rotation mechanics, and web user experience to be perfected first.

---

## 2. Core Architecture & Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | **Django 5.x (Python 3.11+)** | Batteries-included, built-in ORM, admin panel, authentication, and secure session management. |
| **Database** | **SQLite (dev) / PostgreSQL (prod-ready)** | Zero-configuration local development while keeping models fully portable. |
| **Frontend UI** | **Django Templates + HTMX + Modern Vanilla CSS** | Delivers a dynamic SPA-like user experience (instant claiming, status updates, modal forms) without a heavy Node/npm build toolchain. |
| **Scheduling Engine** | **In-process APScheduler (Background Thread)** | Periodically generates recurring chore instances, updates approaching/overdue statuses, and maintains rotation states. |

> Detailed architectural trade-offs, evaluated alternatives, and mitigations are documented in [ADR 001: Technology Stack Selection](adr-001-tech-stack.md).

---

## 3. Domain & Scope Decisions

1. **Single Household Scope**:
   - The application manages a single household unit.
   - All registered housemate users participate in the same pool of chores and leaderboard.
   - Simplifies permissions, URLs, and database queries.

2. **Chore Assignment Mechanics**:
   - **Round-Robin Rotation**: Repeating chores cycle automatically to the next roommate in a defined order upon completion or cycle reset.
   - **Claim Board (Backlog Pool)**: Open, unassigned chores that any housemate can volunteer to take.
   - **Direct Assignment**: Tasks explicitly assigned to a specific housemate with a firm deadline.
   - **Points & Effort Balance**: Chores have point weights (e.g., Quick Trash = 1 pt, Kitchen Deep Clean = 5 pts). A live leaderboard tracks total and monthly contributions.

3. **Hybrid Chore Lifecycle**:
   - **One-off Tasks**: Ad-hoc duties with a single deadline (e.g., "Fix squeaky door", "Replace water filter").
   - **Recurring Templates**: Schedules (Daily, Weekly, Bi-weekly, Monthly) that generate active chore instances automatically.

4. **In-App Deadlines & Visual Alerts**:
   - Clean color-coded indicators for chore urgency on the dashboard:
     - **Normal**: Approaching within comfortable timeline.
     - **Due Soon**: Due within 24 hours (warning highlight).
     - **Overdue**: Passed the deadline without completion (alert badge).

---

## 4. Data Models & Database Schema

```mermaid
erDiagram
    User ||--o| UserProfile : "has"
    UserProfile ||--o{ Chore : "assignee"
    UserProfile ||--o{ Chore : "completed_by"
    ChoreTemplate ||--o{ Chore : "generates"
    Chore ||--o{ ChoreLog : "activity history"

    UserProfile {
        int id PK
        int user_id FK
        int total_points
        boolean is_active_roommate
    }

    ChoreTemplate {
        int id PK
        string title
        text description
        int points
        string frequency "DAILY | WEEKLY | BIWEEKLY | MONTHLY"
        string assignment_strategy "ROUND_ROBIN | CLAIM_POOL | FIXED"
        int default_assignee_id FK
        json rotation_order "List of User IDs"
        int last_assigned_user_id FK
        boolean is_active
    }

    Chore {
        int id PK
        int template_id FK "nullable (null for one-off)"
        string title
        text description
        int points
        string status "PENDING | CLAIMABLE | COMPLETED | OVERDUE"
        int assignee_id FK "nullable"
        datetime due_date
        datetime completed_at
        int completed_by_id FK "nullable"
        datetime created_at
    }

    ChoreLog {
        int id PK
        int chore_id FK
        int user_id FK
        string action "CREATED | CLAIMED | COMPLETED | REASSIGNED | OVERDUE_ALERT"
        datetime timestamp
        text note
    }
```

---

## 5. Web Application User Experience (HTMX + CSS)

### Design & Theme
- **Clean, Modern Aesthetic**: Card-based layouts, dark/light theme support, accessible typography, subtle micro-animations.
- **Dynamic Board**:
  - **Tabs / Filters**: "My Chores", "Available to Claim (Pool)", "All Household Chores", "Completed Recently".
  - **Action Buttons**: Instant HTMX `hx-post` for **[Claim]** and **[Complete]** with smooth DOM replacement (no full-page reload).
  - **Urgency Badges**: Visual indicators for tasks due today and overdue items.
- **House Leaderboard & Stats**:
  - Highlights top contributors and points distribution for the week/month.
  - Visual indicator of effort fairness among roommates.
- **Chore Creation & Management**:
  - Unified modal/page for creating either a one-time task or a recurring template with rotation rules.
- **User Profile**:
  - Personal stats, completed chores history, and account settings.

---

## 6. Project Directory Structure

```text
ai-dev-tools-zoomcamp-2026-hw01/
├── _docs/
│   ├── plan.md                  # Master specification and implementation plan
│   └── adr-001-tech-stack.md    # Architecture Decision Record
├── chore_manager/               # Django project root
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── chores/                      # Main application
│   ├── migrations/
│   ├── templates/
│   │   ├── base.html
│   │   ├── chores/
│   │   │   ├── dashboard.html
│   │   │   ├── partials/
│   │   │   │   ├── chore_card.html
│   │   │   │   ├── chore_list.html
│   │   │   │   ├── claim_pool.html
│   │   │   │   └── leaderboard.html
│   │   │   ├── chore_form.html
│   │   │   └── profile.html
│   │   └── registration/
│   │       └── login.html
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Polished Vanilla CSS design system
│   │   └── js/
│   │       └── main.js
│   ├── management/
│   │   └── commands/
│   │       ├── seed_data.py     # Populates test users and sample chores
│   │       └── process_tasks.py # Manual trigger for recurring chores & status checks
│   ├── services/
│   │   ├── rotation_service.py  # Round-robin and points balance algorithms
│   │   └── scheduler.py         # APScheduler background task manager
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt             # Django, apscheduler, python-dotenv
└── .env.example
```

---

## 7. Step-by-Step Implementation Roadmap

### Phase 1: Environment & Django Foundation
- Initialize virtual environment and create `requirements.txt` (`Django`, `apscheduler`, `python-dotenv`).
- Set up Django project settings, timezone, static files, and `.env` configuration.
- Implement data models (`UserProfile`, `ChoreTemplate`, `Chore`, `ChoreLog`) and run initial migrations.
- Configure Django Admin with filters, search, and inline history logs.

### Phase 2: Core Domain Logic & Rotation Engine
- Implement rotation engine (`rotation_service.py`):
  - Round-robin assignee advancement logic.
  - Claiming and completion workflows with automatic points award.
- Create seed data script (`python manage.py seed_data`) to generate a realistic household with roommates, chores, and history for immediate testing.

### Phase 3: Web Interface & Dynamic Interactions (HTMX)
- Build responsive base layout with modern CSS (design system, cards, typography, badges).
- Build the main Dashboard with dynamic HTMX partials:
  - Chore list by status and personal assignment.
  - Claim pool board with instant one-click claim action.
  - Live household leaderboard showing points and completion counts.
- Add forms for creating one-off tasks and recurring templates.
- Implement User Profile page with personal chore statistics.

### Phase 4: In-Process Automation & Background Scheduler
- Configure `APScheduler` in `chores/apps.py` (with standalone fallback via `manage.py process_tasks`):
  - Generate upcoming instances from active `ChoreTemplate` entries.
  - Check for approaching and overdue deadlines, updating chore statuses automatically.

### Phase 5: Verification & Final Polish
- Test all user flows:
  1. Roommate logs in, creates a chore template and one-off task.
  2. Housemate claims an open chore on the web board via HTMX.
  3. Housemate marks chore done; points are awarded to profile.
  4. Leaderboard updates dynamically.
  5. Recurring chores generate the next rotation cycle automatically.
- Document setup instructions and testing guide in `README.md`.

---

## 8. Future Extensions (Post-MVP)
- **Telegram Bot Integration**: Connect `bot_service.py` and a long-polling worker to send direct message reminders and allow inline claim/done actions.
- **Push Notifications / WebSockets**: Instant updates across open browser tabs without polling.
