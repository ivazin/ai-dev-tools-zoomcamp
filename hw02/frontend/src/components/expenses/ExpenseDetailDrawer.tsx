import React, { useState } from 'react';
import { Expense, Participant } from '../../types';
import { formatMoney, formatExpenseDate } from '../../utils/formatters';
import { Avatar } from '../common/Avatar';
import { Modal } from '../common/Modal';

interface ExpenseDetailDrawerProps {
  expense: Expense | null;
  participants: Participant[];
  isOpen: boolean;
  onClose: () => void;
  onEdit: (expense: Expense) => void;
  onDelete: (id: string) => void;
}

export const ExpenseDetailDrawer: React.FC<ExpenseDetailDrawerProps> = ({
  expense,
  participants,
  isOpen,
  onClose,
  onEdit,
  onDelete,
}) => {
  if (!expense || !isOpen) return null;

  const payer = participants.find((p) => p.id === expense.payerId);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={expense.description}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Total & Payer Banner */}
        <div
          style={{
            background: 'var(--bg-surface-elevated)',
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Paid by</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <Avatar name={payer?.name || 'Unknown'} color={payer?.avatarColor} size={28} />
              <span style={{ fontWeight: 600 }}>{payer?.name}</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {formatExpenseDate(expense.date, expense.createdAt)}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Amount</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>
              {formatMoney(expense.baseAmount)}
            </div>
            {expense.originalCurrency !== 'EUR' && (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {formatMoney(expense.originalAmount, expense.originalCurrency)} (1 {expense.originalCurrency} = {expense.exchangeRate} EUR)
              </div>
            )}
          </div>
        </div>

        {/* Itemized Line Items if present */}
        {expense.isItemized && expense.lineItems && expense.lineItems.length > 0 && (
          <div>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
              RECEIPT BREAKDOWN
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {expense.lineItems.map((li) => {
                const assignedNames = participants
                  .filter((p) => li.consumerIds.includes(p.id))
                  .map((p) => p.name)
                  .join(', ');

                return (
                  <div
                    key={li.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: 'var(--bg-primary)',
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.88rem',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 500 }}>{li.title}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Split among: {assignedNames || 'Everyone'}
                      </div>
                    </div>
                    <div style={{ fontWeight: 600 }}>
                      {formatMoney(li.amount, expense.originalCurrency)}
                    </div>
                  </div>
                );
              })}

              {(expense.taxAmount || expense.tipAmount) && (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)',
                  }}
                >
                  <span>Tax & Tip (Distributed Proportionally)</span>
                  <span>{formatMoney((expense.taxAmount || 0) + (expense.tipAmount || 0), expense.originalCurrency)}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Participant Split Allocation Breakdown */}
        <div>
          <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
            SPLIT SHARE PER PERSON
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {expense.splits.map((s) => {
              const person = participants.find((p) => p.id === s.participantId);
              return (
                <div
                  key={s.participantId}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 4px',
                    borderBottom: '1px solid var(--bg-surface-glass-border)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Avatar name={person?.name || 'User'} color={person?.avatarColor} size={24} />
                    <span style={{ fontSize: '0.9rem' }}>{person?.name}</span>
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                    {formatMoney(s.computedBaseAmount)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Actions: Edit & Delete */}
        <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              onEdit(expense);
              onClose();
            }}
          >
            Edit Expense
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              if (window.confirm(`Delete expense "${expense.description}"?`)) {
                onDelete(expense.id);
                onClose();
              }
            }}
            style={{
              borderColor: 'var(--danger-border)',
              color: 'var(--danger)',
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </Modal>
  );
};
