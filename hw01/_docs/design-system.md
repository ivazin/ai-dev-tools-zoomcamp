# Design System & UI Guidelines

## Philosophy & Technology Stack

The Household Chore Manager delivers a dynamic, responsive web interface using:
- **Semantic HTML5**
- **Vanilla CSS** with CSS Custom Properties (Design Tokens) — zero Node.js/npm dependencies
- **HTMX** for smooth partial swaps and asynchronous actions without full page reloads

---

## Design Tokens (CSS Variables)

Defined in `:root` inside `static/css/styles.css`:

```css
:root {
  /* Color Palette */
  --color-primary: #3b82f6;        /* Modern energetic blue */
  --color-primary-hover: #2563eb;
  --color-success: #10b981;        /* Completed / positive points */
  --color-warning: #f59e0b;        /* Due Soon (within 24h) */
  --color-danger: #ef4444;         /* Overdue */
  --color-neutral-100: #f8fafc;    /* Background surface light */
  --color-neutral-200: #e2e8f0;    /* Border / divider */
  --color-neutral-700: #334155;    /* Muted text */
  --color-neutral-900: #0f172a;    /* Headings / primary text */

  /* Surface & Background */
  --bg-app: #f1f5f9;
  --bg-card: #ffffff;
  --bg-input: #ffffff;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;

  /* Spacing Scale */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Borders & Shadows */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}
```

---

## Component Guidelines

### 1. Chore Cards (`.chore-card`)
- Card containers with rounded corners (`--radius-md`) and subtle shadow (`--shadow-sm`).
- Include:
  - Chore title (`font-weight: 600`)
  - Description snippet
  - Points pill (`.badge-points`)
  - Assignee avatar or initials tag
  - Deadline status indicator badge
  - Direct action button ([Claim] or [Mark Complete])

### 2. Status Badges
Badges communicate chore urgency clearly:
- **Normal:** Subtle neutral/blue styling (`.badge-normal`)
- **Due Soon (within 24 hours):** Amber/warning highlight (`.badge-due-soon`)
- **Overdue:** Red alert badge with bold visual weight (`.badge-overdue`)
- **Completed:** Green badge with completion timestamp (`.badge-completed`)

### 3. Buttons
- `.btn-primary`: Solid blue for primary actions (Create chore, Save).
- `.btn-secondary`: Outlined or light background for cancel/close.
- `.btn-claim`: Vibrant action button for claiming pool tasks.
- `.btn-complete`: Green action button for finishing a chore.
- Every button must have a clear `:hover`, `:focus-visible`, and `:disabled` state.

### 4. Navigation & Household Session Widget
- Persistent top navigation bar displaying:
  - Household name / logo
  - Active links: Dashboard, Claim Pool, Leaderboard
  - Current user avatar, username, and live points counter (e.g. `⭐ 14 pts`)
  - Logout action

### 5. Tabs & Filters
- Clean horizontal tab bar to filter the dashboard:
  - "My Chores"
  - "Available to Claim"
  - "All Household Chores"
  - "Completed"
- Active tab must use a solid accent underline or pill fill.

---

## HTMX Interaction Patterns

1. **Inline Partial Updates:**
   - For actions like claiming or completing a chore, target the card directly:
     ```html
     <button hx-post="/chores/12/claim/"
             hx-target="#chore-12"
             hx-swap="outerHTML">
       Claim Chore
     </button>
     ```
2. **Out-of-Band (OOB) Updates for Navbar Points:**
   - When a chore is completed and points increase, return the updated card HTML along with an out-of-band swap for the user's score in the header:
     ```html
     <div id="user-points-badge" hx-swap-oob="true" class="badge-points">
       ⭐ 18 pts
     </div>
     ```
3. **Loading States (`.htmx-indicator`):**
   - Provide visual feedback on slow network requests using HTMX indicator classes:
     ```html
     <span class="htmx-indicator spinner"></span>
     ```
4. **Graceful Empty States:**
   - When a list has no items (e.g., no available pool chores or zero overdue chores), always display a friendly empty state card rather than a blank whitespace.
