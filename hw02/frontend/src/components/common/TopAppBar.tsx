import React, { useState } from 'react';
import { useEvent } from '../../context/EventContext';
import { Avatar } from './Avatar';
import { Modal } from './Modal';

interface TopAppBarProps {
  onOpenShare: () => void;
  onOpenCreateEvent: () => void;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({ onOpenShare, onOpenCreateEvent }) => {
  const {
    event,
    recentEvents,
    activeParticipant,
    onlineParticipantIds,
    setActiveParticipant,
    switchEvent,
    isMock,
  } = useEvent();
  const [showProfileDrawer, setShowProfileDrawer] = useState(false);
  const [showEventDrawer, setShowEventDrawer] = useState(false);

  if (!event) return null;

  return (
    <>
      <header className="app-header">
        <div className="header-left">
          {/* Clickable Event Selector */}
          <button
            className="event-title-badge"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 6px',
              borderRadius: 'var(--radius-md)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              textAlign: 'left',
              transition: 'background 0.2s',
            }}
            onClick={() => setShowEventDrawer(true)}
            title="Click to switch or create events"
          >
            <span>{event.title}</span>
            <span className="currency-tag">{event.baseCurrency}</span>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              style={{ opacity: 0.7 }}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
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
          </button>
        </div>

        <div className="header-actions">
          {/* Quick Create Event Button */}
          <button
            className="icon-btn"
            onClick={onOpenCreateEvent}
            title="Create a new event"
            aria-label="Create Event"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>

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

      {/* Events Switcher Modal */}
      <Modal
        isOpen={showEventDrawer}
        onClose={() => setShowEventDrawer(false)}
        title="Events"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <button
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            onClick={() => {
              setShowEventDrawer(false);
              onOpenCreateEvent();
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>Create New Event</span>
          </button>

          {recentEvents.length > 0 && (
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Recent Events
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {recentEvents.map((e) => {
                  const isCurrent = e.id === event.id;
                  return (
                    <button
                      key={e.id}
                      className="card-item"
                      style={{
                        borderColor: isCurrent ? 'var(--accent-primary)' : undefined,
                        background: isCurrent ? 'rgba(99, 102, 241, 0.15)' : undefined,
                        cursor: 'pointer',
                        textAlign: 'left',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                      onClick={() => {
                        if (!isCurrent) {
                          switchEvent(e.id);
                        }
                        setShowEventDrawer(false);
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{e.title}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Currency: {e.baseCurrency}
                        </div>
                      </div>
                      {isCurrent ? (
                        <span style={{ color: 'var(--accent-primary)', fontSize: '0.82rem', fontWeight: 600 }}>
                          Current ✓
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                          Switch →
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </Modal>

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
