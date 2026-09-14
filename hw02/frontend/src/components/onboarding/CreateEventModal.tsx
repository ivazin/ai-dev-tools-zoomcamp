import React, { useState } from 'react';
import { CurrencyCode } from '../../types';
import { useEvent } from '../../context/EventContext';
import { Modal } from '../common/Modal';

interface CreateEventModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateEventModal: React.FC<CreateEventModalProps> = ({ isOpen, onClose }) => {
  const { createEvent } = useEvent();
  const [title, setTitle] = useState('');
  const [baseCurrency, setBaseCurrency] = useState<CurrencyCode>('EUR');
  const [creatorName, setCreatorName] = useState('');
  const [participantInput, setParticipantInput] = useState('');
  const [participants, setParticipants] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddParticipant = () => {
    const trimmed = participantInput.trim();
    if (trimmed && !participants.includes(trimmed)) {
      setParticipants([...participants, trimmed]);
      setParticipantInput('');
    }
  };

  const handleRemoveParticipant = (name: string) => {
    setParticipants(participants.filter((p) => p !== name));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !creatorName.trim()) return;

    setIsSubmitting(true);
    try {
      await createEvent({
        title: title.trim(),
        baseCurrency,
        creatorName: creatorName.trim(),
        initialParticipants: participants,
      });
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Event">
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
            Event Title *
          </label>
          <input
            type="text"
            placeholder="e.g. Barcelona Trip, Rome Weekend, Flat 4B"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
            Base Settlement Currency
          </label>
          <select
            value={baseCurrency}
            onChange={(e) => setBaseCurrency(e.target.value as CurrencyCode)}
          >
            <option value="EUR">EUR (€ - Euro)</option>
            <option value="USD">USD ($ - US Dollar)</option>
            <option value="GBP">GBP (£ - British Pound)</option>
            <option value="JPY">JPY (¥ - Japanese Yen)</option>
            <option value="CAD">CAD (CA$ - Canadian Dollar)</option>
            <option value="CHF">CHF (Swiss Franc)</option>
            <option value="AUD">AUD (AU$ - Australian Dollar)</option>
          </select>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
            All debts will be converted & settled in this currency via ECB daily rates.
          </span>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
            Your Name *
          </label>
          <input
            type="text"
            placeholder="e.g. Alex"
            value={creatorName}
            onChange={(e) => setCreatorName(e.target.value)}
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
            Add Other Participants (Optional)
          </label>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <input
              type="text"
              placeholder="Friend's name"
              value={participantInput}
              onChange={(e) => setParticipantInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddParticipant();
                }
              }}
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={handleAddParticipant}
              disabled={!participantInput.trim()}
              style={{ flex: 'none', padding: '10px 14px' }}
            >
              Add
            </button>
          </div>

          {participants.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {participants.map((name) => (
                <span
                  key={name}
                  style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--bg-surface-glass-border)',
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.82rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  {name}
                  <button
                    type="button"
                    onClick={() => handleRemoveParticipant(name)}
                    style={{ color: 'var(--text-muted)', fontSize: '1rem', lineHeight: 1 }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div style={{ marginTop: '8px' }}>
          <button
            type="submit"
            className="btn-primary"
            disabled={!title.trim() || !creatorName.trim() || isSubmitting}
            style={{ width: '100%' }}
          >
            {isSubmitting ? 'Creating Event...' : 'Create Event'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
