import React, { useState, useEffect } from 'react';
import { CurrencyCode, Participant, LineItem, Expense } from '../../types';
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
  expenseToEdit?: Expense | null;
}

export const ExpenseFormModal: React.FC<ExpenseFormModalProps> = ({
  isOpen,
  onClose,
  participants,
  baseCurrency,
  defaultPayerId,
  expenseToEdit,
}) => {
  const { createExpense, updateExpense } = useEvent();
  const [activeTab, setActiveTab] = useState<'quick' | 'itemized'>('quick');

  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState<number>(0);
  const [currency, setCurrency] = useState<CurrencyCode>(baseCurrency);
  const [payerId, setPayerId] = useState<string>(defaultPayerId || participants[0]?.id || '');
  const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0]);

  // Quick split state
  const [splits, setSplits] = useState<Array<{ participantId: string; amount?: number; shares?: number }>>([]);
  const [isQuickSplitValid, setIsQuickSplitValid] = useState(true);

  // Itemized state
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [tax, setTax] = useState(0);
  const [tip, setTip] = useState(0);

  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate form fields when editing an existing expense or opening fresh
  useEffect(() => {
    if (expenseToEdit) {
      setDescription(expenseToEdit.description);
      setAmount(expenseToEdit.originalAmount);
      setCurrency(expenseToEdit.originalCurrency);
      setPayerId(expenseToEdit.payerId);
      setDate(expenseToEdit.date ? expenseToEdit.date.split('T')[0] : new Date().toISOString().split('T')[0]);
      setActiveTab(expenseToEdit.isItemized ? 'itemized' : 'quick');

      if (expenseToEdit.isItemized && expenseToEdit.lineItems) {
        setLineItems(expenseToEdit.lineItems);
        setTax(expenseToEdit.taxAmount || 0);
        setTip(expenseToEdit.tipAmount || 0);
      } else {
        setSplits(
          expenseToEdit.splits.map((s) => ({
            participantId: s.participantId,
            amount: s.amount !== undefined ? s.amount : s.computedBaseAmount,
            shares: s.shares,
          }))
        );
      }
    } else {
      setDescription('');
      setAmount(0);
      setCurrency(baseCurrency);
      setPayerId(defaultPayerId || participants[0]?.id || '');
      setDate(new Date().toISOString().split('T')[0]);
      setActiveTab('quick');
      setLineItems([]);
      setTax(0);
      setTip(0);
      setSplits([]);
      setIsQuickSplitValid(true);
    }
  }, [expenseToEdit, isOpen, baseCurrency, defaultPayerId, participants]);

  if (!isOpen) return null;

  // Real-time exchange rate calculation preview
  const exchangeRate = calculateExchangeRate(currency, baseCurrency);
  const effectiveTotal = activeTab === 'quick'
    ? amount
    : lineItems.reduce((sum, item) => sum + (item.amount || 0), 0) + tax + tip;
  const convertedBaseAmount = Math.round(effectiveTotal * exchangeRate * 100) / 100;

  const isFormValid = Boolean(
    description.trim() &&
    effectiveTotal > 0 &&
    (activeTab === 'itemized' || isQuickSplitValid)
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid || isSubmitting) return;

    setIsSubmitting(true);
    try {
      if (expenseToEdit) {
        // Edit mode
        if (activeTab === 'quick') {
          await updateExpense(expenseToEdit.id, {
            payerId,
            description: description.trim(),
            originalAmount: effectiveTotal,
            originalCurrency: currency,
            isItemized: false,
            date: new Date(date).toISOString(),
            splits,
          });
        } else {
          await updateExpense(expenseToEdit.id, {
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
      } else {
        // Create mode
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
      }
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={expenseToEdit ? 'Edit Expense' : 'Add New Expense'}
    >
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
            initialSplits={expenseToEdit?.splits}
            onSplitsCalculated={(calculatedSplits, isValid) => {
              setSplits(calculatedSplits);
              setIsQuickSplitValid(isValid);
            }}
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
            disabled={!isFormValid || isSubmitting}
            style={{ width: '100%' }}
          >
            {isSubmitting
              ? 'Saving Expense...'
              : expenseToEdit
              ? 'Save Changes'
              : 'Save Expense'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
