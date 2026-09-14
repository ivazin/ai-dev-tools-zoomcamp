import React, { useState } from 'react';
import { CurrencyCode, Participant, LineItem } from '../../types';
import { calculateExchangeRate } from '../../services/currencyRates';
import { useEvent } from '../../context/EventContext';
import { Modal } from '../common/Modal';
import { QuickSplitForm } from './QuickSplitForm';
import { ItemizedReceiptForm } from './ItemizedReceiptForm';
import { formatMoney } from '../../utils/formatters';

interface ExpenseFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  participants: Participant[];
  baseCurrency: CurrencyCode;
  defaultPayerId?: string;
}

export const ExpenseFormModal: React.FC<ExpenseFormModalProps> = ({
  isOpen,
  onClose,
  participants,
  baseCurrency,
  defaultPayerId,
}) => {
  const { createExpense } = useEvent();
  const [activeTab, setActiveTab] = useState<'quick' | 'itemized'>('quick');

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState<number>(0);
  const [currency, setCurrency] = useState<CurrencyCode>(baseCurrency);
  const [payerId, setPayerId] = useState<string>(defaultPayerId || participants[0]?.id || '');
  const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0]);

  // Quick split state
  const [splits, setSplits] = useState<Array<{ participantId: string; amount?: number; shares?: number }>>([]);

  // Itemized state
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [tax, setTax] = useState(0);
  const [tip, setTip] = useState(0);

  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  // Real-time exchange rate calculation preview
  const exchangeRate = calculateExchangeRate(currency, baseCurrency);
  const effectiveTotal = activeTab === 'quick'
    ? amount
    : lineItems.reduce((sum, item) => sum + (item.amount || 0), 0) + tax + tip;
  const convertedBaseAmount = Math.round(effectiveTotal * exchangeRate * 100) / 100;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || effectiveTotal <= 0) return;

    setIsSubmitting(true);
    try {
      if (activeTab === 'quick') {
        await createExpense({
          eventId: participants[0]?.eventId || '',
          payerId,
          description: description.trim(),
          originalAmount: effectiveTotal,
          originalCurrency: currency,
          isItemized: false,
          date: new Date(date).toISOString(),
          splits,
        });
      } else {
        await createExpense({
          eventId: participants[0]?.eventId || '',
          payerId,
          description: description.trim(),
          originalAmount: effectiveTotal,
          originalCurrency: currency,
          isItemized: true,
          date: new Date(date).toISOString(),
          lineItems,
          taxAmount: tax,
          tipAmount: tip,
        });
      }
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Expense">
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Top Segmented Mode Switcher */}
        <div className="segmented-control">
          <button
            type="button"
            className={`segmented-btn ${activeTab === 'quick' ? 'active' : ''}`}
            onClick={() => setActiveTab('quick')}
          >
            Quick Split
          </button>
          <button
            type="button"
            className={`segmented-btn ${activeTab === 'itemized' ? 'active' : ''}`}
            onClick={() => setActiveTab('itemized')}
          >
            Itemized / Receipt
          </button>
        </div>

        {/* Description & Payer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Description *
            </label>
            <input
              type="text"
              placeholder="e.g. Dinner, Taxi, Groceries"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Paid By
              </label>
              <select value={payerId} onChange={(e) => setPayerId(e.target.value)}>
                {participants.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Date
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Amount & Currency (for Quick Split) */}
        {activeTab === 'quick' && (
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Total Amount *
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={amount || ''}
                onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                required
                style={{ fontSize: '1.25rem', fontWeight: 700, flex: 2 }}
              />
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
                style={{ flex: 1 }}
              >
                <option value="EUR">EUR (€)</option>
                <option value="USD">USD ($)</option>
                <option value="GBP">GBP (£)</option>
                <option value="JPY">JPY (¥)</option>
                <option value="CAD">CAD (CA$)</option>
                <option value="CHF">CHF</option>
                <option value="AUD">AUD (AU$)</option>
              </select>
            </div>

            {/* Instant Live ECB Conversion Preview */}
            {currency !== baseCurrency && (
              <div
                style={{
                  fontSize: '0.78rem',
                  color: '#a5b4fc',
                  background: 'rgba(99, 102, 241, 0.1)',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  marginTop: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>ℹ️</span>
                <span>
                  ≈ {formatMoney(convertedBaseAmount, baseCurrency)} (1 {currency} = {exchangeRate} {baseCurrency} via ECB reference rate)
                </span>
              </div>
            )}
          </div>
        )}

        {/* Render Tab specific controls */}
        {activeTab === 'quick' ? (
          <QuickSplitForm
            totalAmount={amount}
            participants={participants}
            onSplitsCalculated={setSplits}
          />
        ) : (
          <ItemizedReceiptForm
            participants={participants}
            currency={currency}
            onItemsChanged={(items, t, tipAmount) => {
              setLineItems(items);
              setTax(t);
              setTip(tipAmount);
            }}
          />
        )}

        <div style={{ marginTop: '8px' }}>
          <button
            type="submit"
            className="btn-primary"
            disabled={!description.trim() || effectiveTotal <= 0 || isSubmitting}
            style={{ width: '100%' }}
          >
            {isSubmitting ? 'Saving Expense...' : 'Save Expense'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
