import React from 'react';

export type ActiveTab = 'expenses' | 'balances' | 'activity';

interface BottomNavBarProps {
  activeTab: ActiveTab;
  onChangeTab: (tab: ActiveTab) => void;
}

export const BottomNavBar: React.FC<BottomNavBarProps> = ({ activeTab, onChangeTab }) => {
  return (
    <nav className="bottom-nav">
      <button
        className={`nav-tab ${activeTab === 'expenses' ? 'active' : ''}`}
        onClick={() => onChangeTab('expenses')}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="2" y="5" width="20" height="14" rx="2" />
          <line x1="2" y1="10" x2="22" y2="10" />
        </svg>
        <span>Expenses</span>
      </button>

      <button
        className={`nav-tab ${activeTab === 'balances' ? 'active' : ''}`}
        onClick={() => onChangeTab('balances')}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
        </svg>
        <span>Balances</span>
      </button>

      <button
        className={`nav-tab ${activeTab === 'activity' ? 'active' : ''}`}
        onClick={() => onChangeTab('activity')}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <span>Activity</span>
      </button>
    </nav>
  );
};
