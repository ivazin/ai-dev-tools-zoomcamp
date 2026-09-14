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
import { SAMPLE_EVENT } from './services/mockData';

const MainApp: React.FC = () => {
  const { event, activeParticipant, loadEvent, isLoading, error } = useEvent();
  const [activeTab, setActiveTab] = useState<ActiveTab>('expenses');
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    // Parse event ID from URL query ?eventId=... or hash or default to seed
    const params = new URLSearchParams(window.location.search);
    const eventIdFromQuery = params.get('eventId');
    loadEvent(eventIdFromQuery || SAMPLE_EVENT.id);
  }, [loadEvent]);

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
        Loading SplitWave...
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
          gap: '12px',
          padding: '24px',
          textAlign: 'center',
        }}
      >
        <h2 style={{ fontSize: '1.2rem', color: 'var(--danger)' }}>Event Not Found</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{error}</p>
        <button className="btn-primary" onClick={() => setIsCreateModalOpen(true)}>
          Create New Event
        </button>
        <CreateEventModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      </div>
    );
  }

  return (
    <>
      <TopAppBar onOpenShare={() => setIsShareModalOpen(true)} />

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
        eventTitle={event?.title || 'SplitWave Event'}
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
