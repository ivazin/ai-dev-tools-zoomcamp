import React, { useState } from 'react';
import { useEvent } from '../../context/EventContext';
import { calculateNetBalances, calculateSimplifiedDebts, calculatePairwiseDebts } from '../../utils/debtEngine';
import { formatMoney } from '../../utils/formatters';
import { Avatar } from '../common/Avatar';
import { TransferCard } from './TransferCard';
import { SettleUpModal } from './SettleUpModal';
import { DebtTransfer } from '../../types';

export const BalancesTab: React.FC = () => {
  const { event } = useEvent();
  const [debtMode, setDebtMode] = useState<'SIMPLIFIED' | 'PAIRWISE'>('SIMPLIFIED');
  const [isSettleModalOpen, setIsSettleModalOpen] = useState(false);
  const [selectedTransfer, setSelectedTransfer] = useState<DebtTransfer | null>(null);

  if (!event) return null;

  const balances = calculateNetBalances(event.participants, event.expenses, event.settlements);
  const simplifiedTransfers = calculateSimplifiedDebts(balances);
  const pairwiseTransfers = calculatePairwiseDebts(event.participants, event.expenses, event.settlements);

  const activeTransfers = debtMode === 'SIMPLIFIED' ? simplifiedTransfers : pairwiseTransfers;

  const handleOpenSettle = (transfer?: DebtTransfer) => {
    setSelectedTransfer(transfer || null);
    setIsSettleModalOpen(true);
  };

  return (
    <div className="tab-content">
      {/* Individual Net Balance Summary */}
      <div>
        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
          PARTICIPANT BALANCES
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {balances.map((b) => {
            const p = event.participants.find((part) => part.id === b.participantId);
            return (
              <div key={b.participantId} className="card-item" style={{ padding: '10px 14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Avatar name={p?.name || 'User'} color={p?.avatarColor} size={34} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>{p?.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Paid {formatMoney(b.totalPaid)} • Owed {formatMoney(b.totalOwed)}
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: '0.95rem',
                      color: b.netBalance > 0.005 ? '#34d399' : b.netBalance < -0.005 ? '#fb7185' : 'var(--text-muted)',
                    }}
                  >
                    {b.netBalance > 0.005
                      ? `+${formatMoney(b.netBalance)}`
                      : b.netBalance < -0.005
                      ? `-${formatMoney(Math.abs(b.netBalance))}`
                      : 'Settled'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Suggested Transfers & Debt Engine Switcher */}
      <div style={{ marginTop: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            HOW TO SETTLE
          </h3>
          <div className="segmented-control" style={{ width: 'auto' }}>
            <button
              className={`segmented-btn ${debtMode === 'SIMPLIFIED' ? 'active' : ''}`}
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={() => setDebtMode('SIMPLIFIED')}
              title="Minimizes overall transactions between all members"
            >
              Simplified
            </button>
            <button
              className={`segmented-btn ${debtMode === 'PAIRWISE' ? 'active' : ''}`}
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={() => setDebtMode('PAIRWISE')}
              title="Maintains direct bilateral debts between each pair"
            >
              Direct
            </button>
          </div>
        </div>

        {activeTransfers.length === 0 ? (
          <div
            style={{
              padding: '30px 16px',
              textAlign: 'center',
              background: 'var(--bg-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--bg-surface-glass-border)',
              color: '#34d399',
              fontSize: '0.95rem',
              fontWeight: 600,
            }}
          >
            🎉 Everyone is settled up! No outstanding transfers.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {activeTransfers.map((t, idx) => (
              <TransferCard
                key={`${t.fromParticipantId}-${t.toParticipantId}-${idx}`}
                transfer={t}
                participants={event.participants}
                onSettle={handleOpenSettle}
              />
            ))}
          </div>
        )}
      </div>

      {/* Manual Settle Up CTA */}
      <div style={{ marginTop: '16px' }}>
        <button
          className="btn-secondary"
          onClick={() => handleOpenSettle()}
          style={{ width: '100%' }}
        >
          + Record Custom Payment
        </button>
      </div>

      {/* Settle Up Modal */}
      <SettleUpModal
        isOpen={isSettleModalOpen}
        onClose={() => {
          setIsSettleModalOpen(false);
          setSelectedTransfer(null);
        }}
        participants={event.participants}
        baseCurrency={event.baseCurrency}
        initialTransfer={selectedTransfer}
      />
    </div>
  );
};
