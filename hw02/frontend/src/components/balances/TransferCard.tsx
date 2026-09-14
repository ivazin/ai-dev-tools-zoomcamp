import React from 'react';
import { DebtTransfer, Participant } from '../../types';
import { formatMoney } from '../../utils/formatters';
import { Avatar } from '../common/Avatar';

interface TransferCardProps {
  transfer: DebtTransfer;
  participants: Participant[];
  onSettle: (transfer: DebtTransfer) => void;
}

export const TransferCard: React.FC<TransferCardProps> = ({
  transfer,
  participants,
  onSettle,
}) => {
  const debtor = participants.find((p) => p.id === transfer.fromParticipantId);
  const creditor = participants.find((p) => p.id === transfer.toParticipantId);

  return (
    <div className="card-item">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Avatar name={debtor?.name || 'Debtor'} color={debtor?.avatarColor} size={36} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontWeight: 600 }}>{debtor?.name}</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>pays</span>
          <Avatar name={creditor?.name || 'Creditor'} color={creditor?.avatarColor} size={28} />
          <span style={{ fontWeight: 600 }}>{creditor?.name}</span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
          {formatMoney(transfer.amount)}
        </span>
        <button
          className="btn-primary"
          style={{ padding: '7px 14px', fontSize: '0.82rem', borderRadius: 'var(--radius-sm)' }}
          onClick={() => onSettle(transfer)}
        >
          Settle
        </button>
      </div>
    </div>
  );
};
