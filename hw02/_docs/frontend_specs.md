# Frontend Specifications: Expense Splitter (PWA)

## 1. Overview & Core Principles

This specification outlines the user journeys, screen states, component hierarchies, and behavioral requirements for the **Expense Splitter** frontend. The application is built as a zero-friction, mobile-first Progressive Web Application (PWA).

### Guiding Principles
* **Zero Barrier to Entry:** Instant event creation, link-sharing with high-entropy IDs, no passwords or account registration.
* **Mobile-First Touch Ergonomics:** Primary interactions, tabs, and action triggers are positioned within natural thumb reach.
* **Instant Clarity:** Always show converted base currencies, net balances, and unambiguous debt settlement routes.
* **Reactive & Collaborative:** Live WebSocket updates, graceful reconnection states, and contextual highlights when changes arrive.

---

## 2. Information Architecture & Navigation

```
                                  ┌───────────────────────────┐
                                  │   Landing / Create Event  │
                                  │       (/ or /create)      │
                                  └─────────────┬─────────────┘
                                                │ (generates event link)
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Invite / Claim Modal    │
                                  │   "Who are you in event?" │
                                  └─────────────┬─────────────┘
                                                │ (stores active participant in localStorage)
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Event Shell (/e/:eventId)                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Top Bar: Event Name | Base Currency Tag | Active Presence Avatars | Share (QR/Link) | Profile  │
├────────────────────────────────┬────────────────────────────────┬───────────────────────────────┤
│       Tab 1: Expenses          │    Tab 2: Balances & Settle    │     Tab 3: Activity Feed      │
│  - Total Spent & "My Balance"  │  - Net Balance per Person      │  - Real-time Audit Timeline   │
│  - Filter/Search Bar           │  - Debt Toggle:                │  - Actor avatars & diff chips │
│  - Chronological Expense Feed  │    [Simplified] vs [Direct]    │  - Timestamp & target links   │
│  - Sticky "+ Add Expense" FAB  │  - Actionable "Settle Up"      │                               │
└────────────────────────────────┴────────────────────────────────┴───────────────────────────────┘
```

---

## 3. Detailed User Scenarios & Screen Specifications

### Scenario 1: Event Creation & Setup
* **Entry Point:** Root URL (`/`).
* **Fields:**
  - Event Title (e.g., "Barcelona Trip 2026", "Apartment Groceries").
  - Base Currency Selector (Default `EUR`, searchable list: USD, GBP, JPY, CAD, CHF, etc.).
  - Initial Participants: dynamic tag list input where creator inputs initial names (creator's name pre-marked with star/badge).
* **Actions:**
  - "Create Event" button $\to$ backend generates 21-char NanoID event URL.
  - Creator's device automatically sets active participant ID to their entered name in `localStorage`.
  - Immediate redirect to `/e/:eventId` with a welcome toast and auto-triggered Share Sheet / QR modal.

---

### Scenario 2: Invitation & Identity Claiming ("Who are you?")
* **Trigger:** A participant opens `/e/:eventId` with no active session in `localStorage`.
* **Behavior:**
  - Interstitial modal overlays the dashboard: *"Welcome to [Event Title]!"*
  - Subtitle: *"Select your name to participate or add yourself."*
  - **Roster List:** Interactive avatar tiles for all existing participants not currently active or marked with an "Is this you?" button.
  - **Add Self Input:** "Not on the list? Enter your name" input field with an "Add & Join" button.
* **Selection Result:**
  - Saves `{ eventId, participantId, participantName, avatarColor }` into `localStorage`.
  - Sends WebSocket `JOIN` packet: `{ type: "JOIN", participantId }`.
  - Closes modal and highlights current user's balance banner at the top of the screen.

---

### Scenario 3: Main Dashboard & Top App Bar
* **Top Navigation Bar:**
  - **Title:** Event Title (tap to edit if authorized or view event info).
  - **Base Currency Badge:** Shows base currency code (e.g., `EUR`).
  - **Presence Bar:** Row of small overlapping avatar circles indicating currently connected participants (green dot for live WebSocket presence).
  - **Share Action Icon:** Opens Share Modal with:
    - 1-click "Copy Invite Link" with visual confirmation checkmark.
    - Rendered high-contrast SVG QR Code for quick in-person phone camera scanning.
    - Web Share API integration on mobile browsers (`navigator.share`).
  - **Profile Avatar:** Shows currently active identity. Tapping opens a quick drawer to "Switch Profile" or "Edit Name/Color".

---

### Scenario 4: Logging an Expense (Modal / Drawer)
* **Trigger:** Persistent Floating Action Button (`+ Add Expense`) on the Expenses tab.
* **Header:** Segmented Control Switcher at the top:
  - `[ Quick Split ]` (Default)
  - `[ Itemized / Receipt ]`

#### Common Fields (Both Modes):
- **Description:** Text field (e.g., "Team Tapas", "Uber to Airport").
- **Currency & Amount:**
  - Amount input with large typography.
  - Currency picker (default: Event Base Currency).
  - **Instant Live ECB Conversion Preview:** If currency $\neq$ base currency, displays dynamic subtext:
    `"≈ €84.50 EUR (1 USD = 0.92 EUR via ECB reference rate)"`.
- **Payer Selector:** Dropdown/carousel of participants (defaults to active user).
- **Date Picker:** Defaults to current date/time.

#### Mode A: Quick Split (Total Amount)
- **Sub-segment Switcher:**
  1. **Equal (Default):** Checkbox list of all participants. All checked by default. Shows live split breakdown: *"€25.00 / person (4 people)"*. Quick toggles: "Select All", "Clear All".
  2. **Exact Amounts:** Numeric input next to each participant. Live validator checks that $\sum \text{exact} = \text{Total Amount}$. Shows remaining unallocated balance with color warning if not zero.
  3. **Percentages / Shares:** Weight multiplier per participant (e.g. 1 share, 2 shares). Real-time calculated amounts displayed beside each person.

#### Mode B: Itemized / Receipt Mode
- **Line Items List:**
  - Dynamic rows: `Item Name`, `Price`, and `Assigned Diners` (multi-select avatar chips).
  - Split line items evenly among assigned diners.
  - Quick "+ Add Item" button with auto-focus on next row.
- **Taxes, Tip & Service Fees:**
  - Inputs for `Tip` (percentage or flat amount) and `Tax` (flat amount or percentage).
  - Calculation engine distributes tax and tip **proportionally** based on each individual diner's item subtotal share.
- **Summary Preview:** Collapsible drawer showing each participant's calculated share before submitting.

---

### Scenario 5: Expense Feed & Expense Details
* **Expenses Tab:**
  - **Summary Hero Card:**
    - Total Event Spend.
    - Personal Net Balance badge:
      - Positive: green chip *"You are owed €42.50"*.
      - Negative: amber/red chip *"You owe €18.20"*.
      - Settled: neutral chip *"All settled up"*.
  - **Chronological List:** Grouped by date (Today, Yesterday, Date).
  - **Expense Card Attributes:**
    - Icon/Category or Payer avatar.
    - Description & Date.
    - Total amount in original currency and base currency.
    - "Lent by [Payer]" and "Your share: €XX.XX".
    - Mode badge: `Itemized` tag if receipt split.
* **Detail & Mutation Flow:**
  - Tapping an item opens the **Expense Details Drawer**:
    - Itemized breakdown table (if itemized) or split share distribution.
    - "Edit Expense" button (re-opens form pre-populated).
    - "Delete Expense" button (with confirmation modal).

---

### Scenario 6: Balances & Debt Settlement Tab
* **Header Switcher:**
  - `[ Simplified Debts (Default) ]` vs `[ Direct / Pairwise Debts ]`.
  - Explanatory tooltip info popover explaining the difference.
* **Net Balances Section:**
  - List of participants with their net positive/negative balances.
* **Suggested Debt Transfers:**
  - Cards formatted as: `[Debtor Avatar] Alice` $\to$ `[Creditor Avatar] Bob`: **€24.50**.
  - Direct "Settle" action button on each card.
* **Settle Up Flow (Modal):**
  - Triggered via "+ Record Settlement" button or "Settle" button on a specific debt card.
  - Fields: Payer (pre-filled), Payee (pre-filled), Amount (pre-filled with exact debt amount, editable), Date.
  - "Confirm Settlement" button records settlement transaction and recalibrates net balances to 0.

---

### Scenario 7: Activity Feed & Audit Trail
* **Activity Tab:**
  - Real-time append-only timeline of all mutations.
  - Entries formatted as conversational audit events:
    - *“Max created 'Dinner at Can Culleretes' (€124.00) — 2 mins ago”*
    - *“Sarah edited 'Groceries' (changed total from €45.00 to €52.00) — 15 mins ago”*
    - *“Alex recorded settlement: Paid Bob €20.00 — 1 hour ago”*
  - Diff highlight: shows before/after pills for edited values.
  - Direct deep link: tapping the activity card jumps to the corresponding expense.

---

### Scenario 8: Real-Time WebSockets & Conflict Handling
* **Live Ingestion:**
  - Listens to `PARTICIPANT_ADDED`, `EXPENSE_CREATED`, `EXPENSE_UPDATED`, `EXPENSE_DELETED`, `SETTLEMENT_RECORDED`.
  - Updated items smoothly highlight with a gentle glow animation.
  - Floating unobtrusive toast notifications for other users' actions (e.g. *"Elena added 'Cab to hotel'"*).
* **Edit Conflict Handling:**
  - If a user has an expense open in the edit modal while another user modifies or deletes it:
    - Display warning alert banner: *"This expense was just modified by [User]. [Review Latest] [Overwrite]"*.
* **Connection Lifecycle & Offline Mode:**
  - Offline banner appears when connection drops: *"Reconnecting to live sync..."*.
  - Service worker caches UI shell and recent event payload in `localStorage` for offline read access.

---

## 4. Frontend Component Hierarchy

```
App
├── ServiceWorkerProvider & WebSocketProvider
├── NotificationToastContainer
└── Router / View Switcher
    ├── CreateEventPage
    │   └── EventSetupForm
    └── EventPage (/e/:eventId)
        ├── InterstitialClaimModal (if no active participant)
        ├── ShareModal (QR code & Link copy)
        ├── TopAppBar
        │   ├── PresenceAvatars
        │   ├── CurrencyBadge
        │   └── ProfileSwitcherDrawer
        ├── BottomNavBar [ Expenses | Balances | Activity ]
        └── TabViews
            ├── ExpensesTab
            │   ├── BalanceHeroCard
            │   ├── ExpenseFilterBar
            │   ├── ExpenseList
            │   │   └── ExpenseCard
            │   ├── ExpenseDetailDrawer
            │   └── AddExpenseFAB
            │       └── ExpenseFormModal (Tabs: QuickSplit vs Itemized)
            │           ├── CurrencyRatePreview
            │           ├── QuickSplitSection (Equal | Exact | Shares)
            │           └── ItemizedSection (LineItems + Tax/Tip Proportional)
            ├── BalancesTab
            │   ├── DebtEngineToggle (Simplified vs Pairwise)
            │   ├── BalanceSummaryList
            │   ├── SuggestedTransfersList
            │   │   └── TransferCard (with Settle CTA)
            │   └── SettleUpModal
            └── ActivityTab
                └── ActivityTimeline
                    └── ActivityFeedItem (Diff views)
```
