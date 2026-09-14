import React, { useState } from 'react';
import { useEvent } from '../../context/EventContext';
import { Avatar } from '../common/Avatar';
import { Modal } from '../common/Modal';

interface IdentityClaimModalProps {
  isOpen: boolean;
}

export const IdentityClaimModal: React.FC<IdentityClaimModalProps> = ({ isOpen }) => {
  const { event, setActiveParticipant, addParticipant } = useEvent();
  const [newParticipantName, setNewParticipantName] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  if (!isOpen || !event) return null;

  const handleAddAndClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newParticipantName.trim()) return;
    setIsAdding(true);
    try {
      const p = await addParticipant(newParticipantName.trim());
      setActiveParticipant(p);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {}} // Non-dismissible until identity is claimed
      title={`Welcome to ${event.title}`}
    >
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
        To personalize your balances and attribute your expenses, choose who you are:
      </p>

      {/* Roster of participants */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', margin: '12px 0' }}>
        {event.participants.map((p) => (
          <button
            key={p.id}
            className="card-item"
            style={{ textAlign: 'left', cursor: 'pointer' }}
            onClick={() => setActiveParticipant(p)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Avatar name={p.name} color={p.avatarColor} size={40} />
              <div>
                <div style={{ fontWeight: 600 }}>{p.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tap to select</div>
              </div>
            </div>
            <span style={{ color: 'var(--accent-primary)', fontSize: '0.9rem', fontWeight: 600 }}>
              It's me →
            </span>
          </button>
        ))}
      </div>

      {/* Add self section */}
      <div style={{ marginTop: '12px', borderTop: '1px solid var(--bg-surface-glass-border)', paddingTop: '16px' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Not listed? Add yourself to this event:
        </p>
        <form onSubmit={handleAddAndClaim} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="Your name"
            value={newParticipantName}
            onChange={(e) => setNewParticipantName(e.target.value)}
            disabled={isAdding}
            autoFocus
          />
          <button
            type="submit"
            className="btn-primary"
            style={{ flex: 'none', padding: '12px 18px' }}
            disabled={!newParticipantName.trim() || isAdding}
          >
            {isAdding ? 'Adding...' : 'Join'}
          </button>
        </form>
      </div>
    </Modal>
  );
};
