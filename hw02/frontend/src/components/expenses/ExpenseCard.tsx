import React from 'react';
import { Expense, Participant } from '../../types';
import { formatMoney, formatRelativeTime } from '../../utils/formatters';
import { Avatar } from '../common/Avatar';

interface ExpenseCardProps {
  expense: Expense;
  participants: Participant[];
  activeParticipantId?: string;
  isRecentlyUpdated?: boolean;
  onClick: () => void;
}

export const ExpenseCard: React.FC<ExpenseCardProps> = ({
  expense,
  participants,
  activeParticipantId,
  isRecentlyUpdated,
  onClick,
}) => {
  const payer = participants.find((p) => p.id === expense.payerId);
  const mySplit = expense.splits.find((s) => s.participantId === activeParticipantId);
  const isPayer = expense.payerId === activeParticipantId;

  return (
    <div
      className={`card-item ${isRecentlyUpdated ? 'glow-update' : ''}`}
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Avatar
          name={payer?.name || 'Unknown'}
          color={payer?.avatarColor}
          size={40}
        />
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontWeight: 600, fontSize: '0.98rem' }}>{expense.description}</span>
            {expense.isItemized && (
              <span
                style={{
                  fontSize: '0.68rem',
                  background: 'rgba(99, 102, 241, 0.2)',
                  color: '#a5b4fc',
                  padding: '1px 5px',
                  borderRadius: '4px',
                }}
              >
                Receipt
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            <span>{isPayer ? 'You paid' : `${payer?.name || 'Someone'} paid`}</span>
            <span> • {formatRelativeTime(expense.date)}</span>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'right' }}>
        <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>
          {formatMoney(expense.baseAmount, 'EUR')}
        </div>
        {expense.originalCurrency !== 'EUR' && (
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            ({formatMoney(expense.originalAmount, expense.originalCurrency)})
          </div>
        )}
        {mySplit && (
          <div
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              color: isPayer ? '#34d399' : '#fb7185',
              marginTop: '2px',
            }}
          >
            {isPayer
              ? `You lent ${formatMoney(expense.baseAmount - mySplit.computedBaseAmount)}`
              : `Your share ${formatMoney(mySplit.computedBaseAmount)}`}
          </div>
        )}
      </div>
    </div>
  );
};
