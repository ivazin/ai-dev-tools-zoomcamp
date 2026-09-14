import React, { useState } from 'react';
import { Participant, DebtTransfer, CurrencyCode } from '../../types';
import { useEvent } from '../../context/EventContext';
import { Modal } from '../common/Modal';
import { formatMoney } from '../../utils/formatters';

interface SettleUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  participants: Participant[];
  baseCurrency: CurrencyCode;
  initialTransfer?: DebtTransfer | null;
}

export const SettleUpModal: React.FC<SettleUpModalProps> = ({
  isOpen,
  onClose,
  participants,
  baseCurrency,
  initialTransfer,
}) => {
  const { createSettlement } = useEvent();
  const [payerId, setPayerId] = useState<string>(
    initialTransfer?.fromParticipantId || participants[0]?.id || ''
  );
  const [payeeId, setPayeeId] = useState<string>(
    initialTransfer?.toParticipantId || participants[1]?.id || ''
  );
  const [amount, setAmount] = useState<number>(initialTransfer?.amount || 0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!payerId || !payeeId || payerId === payeeId || amount <= 0) return;

    setIsSubmitting(true);
    try {
      await createSettlement({
        eventId: participants[0]?.eventId || '',
        fromParticipantId: payerId,
        toParticipantId: payeeId,
        amount,
        currency: baseCurrency,
      });
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Record a Settlement">
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          Record a payment made directly between group members to clear or reduce balances.
        </p>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Paid by (Debtor)
            </label>
            <select value={payerId} onChange={(e) => setPayerId(e.target.value)}>
              {participants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <span style={{ fontSize: '1.2rem', color: 'var(--text-muted)', paddingTop: '16px' }}>→</span>

          <div style={{ flex: 1 }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Paid to (Creditor)
            </label>
            <select value={payeeId} onChange={(e) => setPayeeId(e.target.value)}>
              {participants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
            Settlement Amount ({baseCurrency})
          </label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={amount || ''}
            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
            required
            style={{ fontSize: '1.25rem', fontWeight: 700 }}
          />
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={payerId === payeeId || amount <= 0 || isSubmitting}
          style={{ width: '100%', marginTop: '8px' }}
        >
          {isSubmitting ? 'Recording Settlement...' : `Confirm Payment of ${formatMoney(amount, baseCurrency)}`}
        </button>
      </form>
    </Modal>
  );
};
