import React, { useEffect, useState } from 'react';
import { EventProvider, useEvent } from './context/EventContext';
import { ToastProvider } from './context/ToastContext';
import { TopAppBar } from './components/common/TopAppBar';
import { BottomNavBar, ActiveTab } from './components/common/BottomNavBar';
import { ExpensesTab } from './components/expenses/ExpensesTab';
import { BalancesTab } from './components/balances/BalancesTab';
import { ActivityTab } from './components/activity/ActivityTab';
import { IdentityClaimModal } from './components/onboarding/IdentityClaimModal';
import { ShareModal } from './components/onboarding/ShareModal';
import { CreateEventModal } from './components/onboarding/CreateEventModal';
import { OnboardingView } from './components/onboarding/OnboardingView';

import { getEventIdFromLocation, navigateToHome, navigateToEvent } from './utils/navigation';

const MainApp: React.FC = () => {
  const { event, activeParticipant, loadEvent, isLoading, error } = useEvent();
  const [activeTab, setActiveTab] = useState<ActiveTab>('expenses');
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Parse event ID from /e/:id or fallback to ?eventId=...
  const currentEventId = getEventIdFromLocation();

  useEffect(() => {
    // If URL has an eventId, load it and ensure pretty URL
    if (currentEventId) {
      // Normalize legacy /?eventId=... to pretty /e/:id in address bar
      if (window.location.pathname === '/' && window.location.search.includes('eventId=')) {
        navigateToEvent(currentEventId);
      }
      loadEvent(currentEventId);
    }

    const handlePopState = () => {
      const id = getEventIdFromLocation();
      if (id) {
        loadEvent(id);
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [currentEventId, loadEvent]);

  // Clean root visit: show friendly Onboarding screen
  if (!currentEventId && !event) {
    return (
      <>
        <OnboardingView onOpenCreate={() => setIsCreateModalOpen(true)} />
        <CreateEventModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      </>
    );
  }

  if (isLoading && !event) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          color: 'var(--text-muted)',
        }}
      >
        Loading Tavli...
      </div>
    );
  }

  if (error && !event) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: '16px',
          padding: '24px',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '2.5rem' }}>🔍</div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)' }}>Event Not Found</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '360px', margin: '0 auto' }}>
          We couldn't find this event. It may have expired or the link might be incorrect.
        </p>
        <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
          <button
            className="btn-secondary"
            onClick={() => {
              navigateToHome();
              window.location.reload();
            }}
          >
            Go to Home
          </button>
          <button className="btn-primary" onClick={() => setIsCreateModalOpen(true)}>
            Create New Event
          </button>
        </div>
        <CreateEventModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      </div>
    );
  }

  return (
    <>
      <TopAppBar
        onOpenShare={() => setIsShareModalOpen(true)}
        onOpenCreateEvent={() => setIsCreateModalOpen(true)}
      />

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'expenses' && <ExpensesTab />}
        {activeTab === 'balances' && <BalancesTab />}
        {activeTab === 'activity' && <ActivityTab />}
      </main>

      <BottomNavBar activeTab={activeTab} onChangeTab={setActiveTab} />

      {/* Interstitial Identity Claim Modal if user hasn't claimed identity on this device */}
      <IdentityClaimModal isOpen={!activeParticipant} />

      {/* Share Modal (QR + Link) */}
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        eventTitle={event?.title || 'Tavli Event'}
      />

      {/* Create New Event Modal */}
      <CreateEventModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </>
  );
};

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <EventProvider>
        <MainApp />
      </EventProvider>
    </ToastProvider>
  );
};

export default App;
