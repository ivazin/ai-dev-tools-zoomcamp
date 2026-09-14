import React, { useState } from 'react';
import { Participant, SplitType } from '../../types';
import { calculateEqualSplit, calculateExactSplit, calculateSharesSplit } from '../../utils/splits';
import { formatMoney } from '../../utils/formatters';

interface QuickSplitFormProps {
  totalAmount: number;
  participants: Participant[];
  onSplitsCalculated: (splits: Array<{ participantId: string; amount?: number; shares?: number }>) => void;
}

export const QuickSplitForm: React.FC<QuickSplitFormProps> = ({
  totalAmount,
  participants,
  onSplitsCalculated,
}) => {
  const [splitType, setSplitType] = useState<SplitType>('EQUAL');
  const [selectedIds, setSelectedIds] = useState<string[]>(participants.map((p) => p.id));
  const [exactValues, setExactValues] = useState<Record<string, number>>({});
  const [sharesValues, setSharesValues] = useState<Record<string, number>>({});

  // Sync Equal splits
  const handleToggleParticipant = (id: string) => {
    let next: string[];
    if (selectedIds.includes(id)) {
      next = selectedIds.filter((pId) => pId !== id);
    } else {
      next = [...selectedIds, id];
    }
    setSelectedIds(next);
    const splits = calculateEqualSplit(totalAmount, next);
    onSplitsCalculated(splits.map((s) => ({ participantId: s.participantId, amount: s.computedBaseAmount })));
  };

  const handleExactChange = (id: string, val: number) => {
    const next = { ...exactValues, [id]: val };
    setExactValues(next);
    const splits = calculateExactSplit(next);
    onSplitsCalculated(splits.map((s) => ({ participantId: s.participantId, amount: s.computedBaseAmount })));
  };

  const handleSharesChange = (id: string, val: number) => {
    const next = { ...sharesValues, [id]: val };
    setSharesValues(next);
    const splits = calculateSharesSplit(totalAmount, next);
    onSplitsCalculated(splits.map((s) => ({ participantId: s.participantId, shares: s.shares })));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Sub Split-type toggle */}
      <div className="segmented-control">
        <button
          type="button"
          className={`segmented-btn ${splitType === 'EQUAL' ? 'active' : ''}`}
          onClick={() => {
            setSplitType('EQUAL');
            const splits = calculateEqualSplit(totalAmount, selectedIds);
            onSplitsCalculated(splits.map((s) => ({ participantId: s.participantId, amount: s.computedBaseAmount })));
          }}
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {participants.map((p) => (
            <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ flex: 1, fontSize: '0.9rem' }}>{p.name}</span>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                style={{ width: '110px', textAlign: 'right' }}
                value={exactValues[p.id] || ''}
                onChange={(e) => handleExactChange(p.id, parseFloat(e.target.value) || 0)}
              />
            </div>
          ))}
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
