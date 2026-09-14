import React, { useState } from 'react';
import { Participant, LineItem } from '../../types';
import { formatMoney } from '../../utils/formatters';

interface ItemizedReceiptFormProps {
  participants: Participant[];
  currency: string;
  onItemsChanged: (items: LineItem[], tax: number, tip: number) => void;
}

export const ItemizedReceiptForm: React.FC<ItemizedReceiptFormProps> = ({
  participants,
  currency,
  onItemsChanged,
}) => {
  const [items, setItems] = useState<LineItem[]>([
    { id: '1', title: 'Main Dish', amount: 0, consumerIds: participants.map((p) => p.id) },
  ]);
  const [tax, setTax] = useState<number>(0);
  const [tip, setTip] = useState<number>(0);

  const notifyChange = (updatedItems: LineItem[], updatedTax: number, updatedTip: number) => {
    onItemsChanged(updatedItems, updatedTax, updatedTip);
  };

  const handleAddItem = () => {
    const newItem: LineItem = {
      id: Math.random().toString(36).substring(2, 9),
      title: '',
      amount: 0,
      consumerIds: participants.map((p) => p.id),
    };
    const next = [...items, newItem];
    setItems(next);
    notifyChange(next, tax, tip);
  };

  const handleRemoveItem = (id: string) => {
    const next = items.filter((i) => i.id !== id);
    setItems(next);
    notifyChange(next, tax, tip);
  };

  const handleUpdateItem = (id: string, field: 'title' | 'amount', val: string | number) => {
    const next = items.map((item) => (item.id === id ? { ...item, [field]: val } : item));
    setItems(next);
    notifyChange(next, tax, tip);
  };

  const handleToggleConsumer = (itemId: string, participantId: string) => {
    const next = items.map((item) => {
      if (item.id !== itemId) return item;
      const ids = item.consumerIds.includes(participantId)
        ? item.consumerIds.filter((id) => id !== participantId)
        : [...item.consumerIds, participantId];
      return { ...item, consumerIds: ids };
    });
    setItems(next);
    notifyChange(next, tax, tip);
  };

  const itemsSubtotal = items.reduce((acc, item) => acc + (item.amount || 0), 0);
  const grandTotal = itemsSubtotal + tax + tip;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
        Add dishes/items from the receipt and assign who enjoyed them:
      </div>

      {items.map((item, index) => (
        <div
          key={item.id}
          style={{
            background: 'var(--bg-primary)',
            border: '1px solid var(--bg-surface-glass-border)',
            borderRadius: 'var(--radius-md)',
            padding: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              placeholder={`Item #${index + 1} (e.g. Pizza)`}
              value={item.title}
              onChange={(e) => handleUpdateItem(item.id, 'title', e.target.value)}
              style={{ flex: 2 }}
            />
            <input
              type="number"
              step="0.01"
              placeholder="0.00"
              value={item.amount || ''}
              onChange={(e) => handleUpdateItem(item.id, 'amount', parseFloat(e.target.value) || 0)}
              style={{ flex: 1, textAlign: 'right' }}
            />
            {items.length > 1 && (
              <button
                type="button"
                className="icon-btn"
                onClick={() => handleRemoveItem(item.id)}
                style={{ width: '32px', height: '32px' }}
              >
                ×
              </button>
            )}
          </div>

          {/* Consumer Multi-select chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Split by:</span>
            {participants.map((p) => {
              const isAssigned = item.consumerIds.includes(p.id);
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleToggleConsumer(item.id, p.id)}
                  style={{
                    fontSize: '0.75rem',
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: isAssigned ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
                    color: isAssigned ? '#ffffff' : 'var(--text-secondary)',
                    border: '1px solid var(--bg-surface-glass-border)',
                    cursor: 'pointer',
                  }}
                >
                  {p.name}
                </button>
              );
            })}
          </div>
        </div>
      ))}

      <button
        type="button"
        className="btn-secondary"
        onClick={handleAddItem}
        style={{ padding: '10px', fontSize: '0.85rem' }}
      >
        + Add Another Item
      </button>

      {/* Tax & Tip Row */}
      <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Tax Amount
          </label>
          <input
            type="number"
            step="0.01"
            placeholder="0.00"
            value={tax || ''}
            onChange={(e) => {
              const val = parseFloat(e.target.value) || 0;
              setTax(val);
              notifyChange(items, val, tip);
            }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Tip Amount
          </label>
          <input
            type="number"
            step="0.01"
            placeholder="0.00"
            value={tip || ''}
            onChange={(e) => {
              const val = parseFloat(e.target.value) || 0;
              setTip(val);
              notifyChange(items, tax, val);
            }}
          />
        </div>
      </div>

      {/* Total calculation indicator */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          padding: '10px 14px',
          background: 'var(--bg-surface-elevated)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.9rem',
          fontWeight: 600,
        }}
      >
        <span>Calculated Total ({currency}):</span>
        <span style={{ color: 'var(--accent-primary)' }}>{formatMoney(grandTotal, currency as any)}</span>
      </div>
    </div>
  );
};
