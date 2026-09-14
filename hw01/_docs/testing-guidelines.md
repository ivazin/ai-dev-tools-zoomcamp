# Testing Guidelines

## Overview

This project uses **pytest** with **pytest-django** as the testing framework.
All testing tasks are executed using `uv`.

---

## Commands

```bash
# Run the entire test suite
uv run pytest

# Run a specific test file
uv run pytest tests/test_models.py

# Run a specific test function or class
uv run pytest -k test_round_robin_advances_to_next_roommate

# Run with verbose output and print statements
uv run pytest -v -s

# Run with test coverage
uv run pytest --cov=chores
```

---

## Test Directory Structure

All tests live in the root `tests/` directory:

```text
tests/
├── conftest.py               # Shared fixtures (users, housemates, chore templates)
├── test_models.py            # Data model field validations, relationships, str methods
├── test_rotation.py          # Rotation algorithm & assignment edge cases
├── test_chore_service.py     # Claiming, completing, points awarding, log auditing
├── test_views.py             # Dashboard, login/logout, profile, claim pool views
├── test_scheduler.py         # Recurring chore generation & overdue status detection
└── test_integration.py       # End-to-end multi-roommate workflow scenarios
```

---

## Core Testing Principles

1. **Verify Against Acceptance Criteria:**
   Every test must map to specific acceptance criteria defined in the groomed GitHub issue.

2. **One Behavioral Assertion per Test:**
   Keep tests focused and readable. A failure should instantly indicate what behavior broke.
   - Name format: `test_<action_or_condition>_<expected_result>`
   - Example: `test_claim_chore_assigns_user_and_creates_log`

3. **Database Isolation (`@pytest.mark.django_db`):**
   Mark any test that reads or writes to the database with `@pytest.mark.django_db`. Tests must never depend on state from prior tests.

4. **Cover Unhappy Paths & Edge Cases:**
   In addition to standard flows, test boundary conditions:
   - Empty lists (e.g. no active roommates available for rotation)
   - Inactive roommates excluded from assignments
   - Duplicate operations (e.g. attempting to claim an already-claimed chore, double-completing)
   - Time transitions (e.g. task due in 23 hours marked "Due Soon", past due marked "Overdue")

5. **Test Services Directly:**
   Business logic resides in `chores/services/`. Test domain rules (points calculation, rotation sequence, status checks) at the unit level before writing view-level integration tests.

6. **Testing HTMX & View Endpoints:**
   - Use Django's `client` to issue GET and POST requests.
   - For HTMX interactions, include the `HTTP_HX_REQUEST="true"` header.
   - Assert both the HTTP status code (typically `200` or `204`) and the presence of expected HTML partial snippets.
   - When headers like `HX-Trigger` or `HX-Redirect` are emitted, verify their values.

7. **Avoid Over-Mocking:**
   Use real SQLite database operations and Django model instances rather than mocking ORM queries. Mock only external system interactions (e.g., time/clocks when simulating future dates, or background scheduler triggers).
