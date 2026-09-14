import React, { useState, useEffect } from 'react';
import { Participant, SplitType } from '../../types';
import {
  calculateEqualSplit,
  calculateExactSplit,
  calculateSharesSplit,
  validateExactSplit,
} from '../../utils/splits';
import { formatMoney } from '../../utils/formatters';

interface QuickSplitFormProps {
  totalAmount: number;
  participants: Participant[];
  initialSplitType?: SplitType;
  initialSplits?: Array<{ participantId: string; amount?: number; shares?: number }>;
  onSplitsCalculated: (
    splits: Array<{ participantId: string; amount?: number; shares?: number }>,
    isValid: boolean
  ) => void;
}

export const QuickSplitForm: React.FC<QuickSplitFormProps> = ({
  totalAmount,
  participants,
  initialSplitType = 'EQUAL',
  initialSplits,
  onSplitsCalculated,
}) => {
  const [splitType, setSplitType] = useState<SplitType>(initialSplitType);
  const [selectedIds, setSelectedIds] = useState<string[]>(
    initialSplits && initialSplits.length > 0
      ? initialSplits.map((s) => s.participantId)
      : participants.map((p) => p.id)
  );
  const [exactValues, setExactValues] = useState<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    if (initialSplits) {
      initialSplits.forEach((s) => {
        if (s.amount !== undefined) {
          map[s.participantId] = s.amount;
        }
      });
    }
    return map;
  });
  const [sharesValues, setSharesValues] = useState<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    if (initialSplits) {
      initialSplits.forEach((s) => {
        if (s.shares !== undefined) {
          map[s.participantId] = s.shares;
        }
      });
    }
    return map;
  });

  // Calculate validation for exact mode
  const exactValidation = validateExactSplit(totalAmount, exactValues);

  // Sync state changes upward
  useEffect(() => {
    if (splitType === 'EQUAL') {
      const splits = calculateEqualSplit(totalAmount, selectedIds);
      onSplitsCalculated(
        splits.map((s) => ({ participantId: s.participantId, amount: s.computedBaseAmount })),
        selectedIds.length > 0
      );
    } else if (splitType === 'EXACT') {
      const splits = calculateExactSplit(exactValues);
      onSplitsCalculated(
        splits.map((s) => ({ participantId: s.participantId, amount: s.computedBaseAmount })),
        exactValidation.isValid
      );
    } else if (splitType === 'SHARES') {
      const splits = calculateSharesSplit(totalAmount, sharesValues);
      const hasShares = Object.values(sharesValues).some((s) => s > 0);
      onSplitsCalculated(
        splits.map((s) => ({ participantId: s.participantId, shares: s.shares })),
        hasShares
      );
    }
  }, [splitType, totalAmount, selectedIds, exactValues, sharesValues, exactValidation.isValid]);

  // Sync Equal splits
  const handleToggleParticipant = (id: string) => {
    let next: string[];
    if (selectedIds.includes(id)) {
      next = selectedIds.filter((pId) => pId !== id);
    } else {
      next = [...selectedIds, id];
    }
    setSelectedIds(next);
  };

  const handleExactChange = (id: string, val: number) => {
    setExactValues((prev) => ({ ...prev, [id]: isNaN(val) ? 0 : val }));
  };

  const handleFillRemainder = (id: string) => {
    // Calculate current total excluding this participant
    const currentOthers = Object.entries(exactValues)
      .filter(([pId]) => pId !== id)
      .reduce((sum, [, amount]) => sum + (isNaN(amount) ? 0 : amount), 0);
    const remainder = Math.max(0, Math.round((totalAmount - currentOthers) * 100) / 100);
    setExactValues((prev) => ({ ...prev, [id]: remainder }));
  };

  const handleDistributeRemainingEqually = () => {
    const unallocated = exactValidation.remainingAmount;
    if (unallocated <= 0) return;

    // Find participants with 0 or unassigned values, or all participants
    const targetIds = participants.map((p) => p.id);
    const equalPortions = calculateEqualSplit(unallocated, targetIds);

    const next = { ...exactValues };
    equalPortions.forEach((portion) => {
      next[portion.participantId] = Math.round(((next[portion.participantId] || 0) + portion.computedBaseAmount) * 100) / 100;
    });
    setExactValues(next);
  };

  const handleSharesChange = (id: string, val: number) => {
    setSharesValues((prev) => ({ ...prev, [id]: val }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Sub Split-type toggle */}
      <div className="segmented-control">
        <button
          type="button"
          className={`segmented-btn ${splitType === 'EQUAL' ? 'active' : ''}`}
          onClick={() => setSplitType('EQUAL')}
        >
          Equally
        </button>
        <button
          type="button"
          className={`segmented-btn ${splitType === 'EXACT' ? 'active' : ''}`}
          onClick={() => setSplitType('EXACT')}
        >
          Exact
        </button>
        <button
          type="button"
          className={`segmented-btn ${splitType === 'SHARES' ? 'active' : ''}`}
          onClick={() => setSplitType('SHARES')}
        >
          Shares
        </button>
      </div>

      {/* EQUAL MODE */}
      {splitType === 'EQUAL' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            <span>Split between {selectedIds.length} diners</span>
            <span>{selectedIds.length > 0 ? `${formatMoney(totalAmount / selectedIds.length)} / person` : 'None'}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {participants.map((p) => {
              const isChecked = selectedIds.includes(p.id);
              return (
                <label
                  key={p.id}
                  className="card-item"
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    borderColor: isChecked ? 'var(--accent-primary)' : undefined,
                  }}
                >
                  <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{p.name}</span>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handleToggleParticipant(p.id)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--accent-primary)' }}
                  />
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* EXACT MODE */}
      {splitType === 'EXACT' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Validation Assistant Banner */}
          <div
            style={{
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${
                exactValidation.isValid
                  ? 'var(--success-border)'
                  : exactValidation.remainingAmount > 0
                  ? 'rgba(245, 158, 11, 0.4)'
                  : 'var(--danger-border)'
              }`,
              background: exactValidation.isValid
                ? 'var(--success-bg)'
                : exactValidation.remainingAmount > 0
                ? 'var(--warning-bg)'
                : 'var(--danger-bg)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>
                {exactValidation.isValid ? (
                  <span style={{ color: '#34d399' }}>✓ Sum matches total ({formatMoney(totalAmount)})</span>
                ) : exactValidation.remainingAmount > 0 ? (
                  <span style={{ color: '#fbbf24' }}>
                    Remaining: {formatMoney(exactValidation.remainingAmount)} of {formatMoney(totalAmount)}
                  </span>
                ) : (
                  <span style={{ color: '#fb7185' }}>
                    Over allocated by {formatMoney(Math.abs(exactValidation.remainingAmount))}!
                  </span>
                )}
              </span>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Entered: {formatMoney(exactValidation.totalAllocated)}
              </span>
            </div>

            {exactValidation.remainingAmount > 0 && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                <button
                  type="button"
                  onClick={handleDistributeRemainingEqually}
                  style={{
                    fontSize: '0.75rem',
                    color: '#a5b4fc',
                    background: 'rgba(99, 102, 241, 0.2)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontWeight: 600,
                  }}
                >
                  Split remaining {formatMoney(exactValidation.remainingAmount)} equally
                </button>
              </div>
            )}
          </div>

          {/* Participant exact inputs with Quick-Fill Remaining helpers */}
          {participants.map((p) => {
            const val = exactValues[p.id] || 0;
            return (
              <div
                key={p.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  background: 'var(--bg-surface-elevated)',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--bg-surface-glass-border)',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{p.name}</div>
                  {exactValidation.remainingAmount > 0 && val === 0 && (
                    <button
                      type="button"
                      onClick={() => handleFillRemainder(p.id)}
                      style={{
                        fontSize: '0.72rem',
                        color: 'var(--accent-primary)',
                        padding: 0,
                        textDecoration: 'underline',
                        background: 'none',
                      }}
                    >
                      Fill remaining ({formatMoney(exactValidation.remainingAmount)})
                    </button>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    style={{ width: '100px', textAlign: 'right', padding: '8px 10px' }}
                    value={exactValues[p.id] !== undefined && exactValues[p.id] !== 0 ? exactValues[p.id] : (exactValues[p.id] === 0 ? '' : '')}
                    onChange={(e) => handleExactChange(p.id, parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* SHARES MODE */}
      {splitType === 'SHARES' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {participants.map((p) => (
            <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ flex: 1, fontSize: '0.9rem' }}>{p.name}</span>
              <input
                type="number"
                min="0"
                step="1"
                placeholder="1"
                style={{ width: '90px', textAlign: 'center' }}
                value={sharesValues[p.id] || ''}
                onChange={(e) => handleSharesChange(p.id, parseInt(e.target.value, 10) || 0)}
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>shares</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
