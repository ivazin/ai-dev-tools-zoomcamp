import React from 'react';
import { useEvent } from '../../context/EventContext';
import { SAMPLE_EVENT } from '../../services/mockData';

interface OnboardingViewProps {
  onOpenCreate: () => void;
}

export const OnboardingView: React.FC<OnboardingViewProps> = ({ onOpenCreate }) => {
  const { recentEvents, switchEvent } = useEvent();

  const handleOpenDemo = () => {
    switchEvent(SAMPLE_EVENT.id);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 20px',
        background: 'radial-gradient(circle at 50% 20%, rgba(99, 102, 241, 0.18) 0%, rgba(15, 23, 42, 0) 70%)',
      }}
    >
      <div
        style={{
          maxWidth: '460px',
          width: '100%',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
        }}
      >
        {/* Brand Icon & Name */}
        <div>
          <div
            style={{
              width: '68px',
              height: '68px',
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 32px rgba(99, 102, 241, 0.35)',
              marginBottom: '16px',
            }}
          >
            <span style={{ fontSize: '2rem' }}>⚡</span>
          </div>
          <h1
            style={{
              fontSize: '2.4rem',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              background: 'linear-gradient(to right, #fff, #cbd5e1)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '8px',
            }}
          >
            Tavli
          </h1>
          <p
            style={{
              fontSize: '1.05rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
              margin: '0 auto',
            }}
          >
            Collaborative expense splitting with zero friction.
            <br />
            No accounts or passwords required.
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
          <button
            className="btn-primary"
            style={{
              padding: '15px 20px',
              fontSize: '1rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
            }}
            onClick={onOpenCreate}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>Create New Event</span>
          </button>

          <button
            className="btn-secondary"
            style={{
              padding: '13px 20px',
              fontSize: '0.95rem',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
            onClick={handleOpenDemo}
          >
            <span>🌴 Explore Demo Event (Barcelona)</span>
          </button>
        </div>

        {/* Recent Events on this device */}
        {recentEvents.length > 0 && (
          <div style={{ width: '100%', textAlign: 'left', marginTop: '12px' }}>
            <div
              style={{
                fontSize: '0.78rem',
                color: 'var(--text-muted)',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                marginBottom: '10px',
              }}
            >
              Your Recent Events
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentEvents.map((ev) => (
                <button
                  key={ev.id}
                  className="card-item"
                  style={{
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    textAlign: 'left',
                  }}
                  onClick={() => switchEvent(ev.id)}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{ev.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Currency: {ev.baseCurrency}
                    </div>
                  </div>
                  <span style={{ color: 'var(--accent-primary)', fontSize: '0.85rem', fontWeight: 600 }}>
                    Open →
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Feature Highlights Footer */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '20px',
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            marginTop: '8px',
          }}
        >
          <span>✨ Dish-by-Dish Itemized</span>
          <span>•</span>
          <span>⚡ Live Debt Settlement</span>
          <span>•</span>
          <span>💶 Real ECB FX Rates</span>
        </div>
      </div>
    </div>
  );
};
