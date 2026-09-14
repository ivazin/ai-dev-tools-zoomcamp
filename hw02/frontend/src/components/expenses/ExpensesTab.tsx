import React, { useState } from 'react';
import { useEvent } from '../../context/EventContext';
import { calculateNetBalances } from '../../utils/debtEngine';
import { formatMoney } from '../../utils/formatters';
import { ExpenseCard } from './ExpenseCard';
import { ExpenseDetailDrawer } from './ExpenseDetailDrawer';
import { ExpenseFormModal } from './ExpenseFormModal';
import { Expense } from '../../types';

export const ExpensesTab: React.FC = () => {
  const { event, activeParticipant, deleteExpense, lastUpdatedItemId } = useEvent();
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  if (!event) return null;

  // Calculate user's personal net balance
  const balances = calculateNetBalances(event.participants, event.expenses, event.settlements);
  const myBalance = activeParticipant
    ? balances.find((b) => b.participantId === activeParticipant.id)?.netBalance || 0
    : 0;

  const totalEventSpend = event.expenses.reduce((acc, exp) => acc + exp.baseAmount, 0);

  const filteredExpenses = event.expenses.filter((exp) =>
    exp.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="tab-content">
      {/* Hero Spend & Balance Card */}
      <div className="balance-hero-card">
        <div className="hero-balance-row">
          <div>
            <div className="hero-label">Total Spent</div>
            <div className="hero-amount">{formatMoney(totalEventSpend, event.baseCurrency)}</div>
          </div>
          {activeParticipant && (
            <div style={{ textAlign: 'right' }}>
              <div className="hero-label">Your Balance</div>
              <div style={{ marginTop: '4px' }}>
                {myBalance > 0.005 ? (
                  <span className="status-badge owed">
                    You are owed {formatMoney(myBalance, event.baseCurrency)}
                  </span>
                ) : myBalance < -0.005 ? (
                  <span className="status-badge owes">
                    You owe {formatMoney(Math.abs(myBalance), event.baseCurrency)}
                  </span>
                ) : (
                  <span className="status-badge settled">All settled up</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filter / Search Bar */}
      {event.expenses.length > 3 && (
        <div>
          <input
            type="text"
            placeholder="Search expenses..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ padding: '8px 12px', fontSize: '0.85rem' }}
          />
        </div>
      )}

      {/* Expense List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {filteredExpenses.length === 0 ? (
          <div
            style={{
              padding: '40px 20px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '0.9rem',
            }}
          >
            {searchQuery ? 'No expenses match your search.' : 'No expenses yet. Tap "+ Add Expense" to start!'}
          </div>
        ) : (
          filteredExpenses.map((exp) => (
            <ExpenseCard
              key={exp.id}
              expense={exp}
              participants={event.participants}
              activeParticipantId={activeParticipant?.id}
              isRecentlyUpdated={lastUpdatedItemId === exp.id}
              onClick={() => setSelectedExpense(exp)}
            />
          ))
        )}
      </div>

      {/* Sticky Floating Action Button */}
      <button
        className="fab-add"
        onClick={() => setIsFormOpen(true)}
        aria-label="Add Expense"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        <span>Add Expense</span>
      </button>

      {/* Expense Detail Drawer */}
      <ExpenseDetailDrawer
        expense={selectedExpense}
        participants={event.participants}
        isOpen={Boolean(selectedExpense)}
        onClose={() => setSelectedExpense(null)}
        onDelete={deleteExpense}
      />

      {/* Expense Creation Form Modal */}
      <ExpenseFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        participants={event.participants}
        baseCurrency={event.baseCurrency}
        defaultPayerId={activeParticipant?.id}
      />
    </div>
  );
};
