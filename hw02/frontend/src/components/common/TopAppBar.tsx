import React, { useState } from 'react';
import { useEvent } from '../../context/EventContext';
import { Avatar } from './Avatar';
import { Modal } from './Modal';

interface TopAppBarProps {
  onOpenShare: () => void;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({ onOpenShare }) => {
  const { event, activeParticipant, onlineParticipantIds, setActiveParticipant, isMock } = useEvent();
  const [showProfileDrawer, setShowProfileDrawer] = useState(false);

  if (!event) return null;

  return (
    <>
      <header className="app-header">
        <div className="header-left">
          <div className="event-title-badge">
            <span>{event.title}</span>
            <span className="currency-tag">{event.baseCurrency}</span>
            {isMock && (
              <span
                style={{
                  fontSize: '0.65rem',
                  background: 'rgba(245, 158, 11, 0.2)',
                  color: '#fbbf24',
                  padding: '2px 5px',
                  borderRadius: '4px',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                }}
                title="Running on centralized mock services layer"
              >
                MOCK
              </span>
            )}
          </div>
        </div>

        <div className="header-actions">
          {/* Active Online Presence Avatars */}
          <div className="presence-cluster" title="Online participants">
            {event.participants
              .filter((p) => onlineParticipantIds.includes(p.id))
              .slice(0, 3)
              .map((p) => (
                <div key={p.id} className="presence-avatar-wrap">
                  <Avatar name={p.name} color={p.avatarColor} size={28} />
                  <span className="presence-dot" />
                </div>
              ))}
          </div>

          {/* Share QR & Link */}
          <button
            className="icon-btn"
            onClick={onOpenShare}
            title="Share invite link or QR code"
            aria-label="Share"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="18" cy="5" r="3" />
              <circle cx="6" cy="12" r="3" />
              <circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
          </button>

          {/* Current Profile Switcher */}
          {activeParticipant ? (
            <button
              style={{ padding: 0 }}
              onClick={() => setShowProfileDrawer(true)}
              title={`Active: ${activeParticipant.name} (Tap to switch)`}
              aria-label="Profile"
            >
              <Avatar
                name={activeParticipant.name}
                color={activeParticipant.avatarColor}
                size={32}
              />
            </button>
          ) : (
            <button
              className="icon-btn"
              onClick={() => setShowProfileDrawer(true)}
              aria-label="Select profile"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </button>
          )}
        </div>
      </header>

      {/* Profile Switcher Modal */}
      <Modal
        isOpen={showProfileDrawer}
        onClose={() => setShowProfileDrawer(false)}
        title="Switch Active Profile"
      >
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '12px' }}>
          Select who is using this device to attribute your expenses and personalize your debt balances.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {event.participants.map((p) => (
            <button
              key={p.id}
              className="card-item"
              style={{
                borderColor: activeParticipant?.id === p.id ? 'var(--accent-primary)' : undefined,
                background: activeParticipant?.id === p.id ? 'rgba(99, 102, 241, 0.15)' : undefined,
                cursor: 'pointer',
                textAlign: 'left',
              }}
              onClick={() => {
                setActiveParticipant(p);
                setShowProfileDrawer(false);
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Avatar name={p.name} color={p.avatarColor} size={36} />
                <span style={{ fontWeight: 600 }}>{p.name}</span>
              </div>
              {activeParticipant?.id === p.id && (
                <span style={{ color: 'var(--accent-primary)', fontSize: '0.85rem', fontWeight: 600 }}>
                  Active ✓
                </span>
              )}
            </button>
          ))}
        </div>
      </Modal>
    </>
  );
};
