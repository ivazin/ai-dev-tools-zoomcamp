import React from 'react';
import { useEvent } from '../../context/EventContext';
import { formatRelativeTime } from '../../utils/formatters';
import { Avatar } from '../common/Avatar';

export const ActivityTab: React.FC = () => {
  const { event } = useEvent();

  if (!event) return null;

  return (
    <div className="tab-content">
      <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
        REAL-TIME AUDIT LOG
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {event.activityLogs.map((log) => {
          const actor = event.participants.find((p) => p.id === log.actorId);

          let description = '';
          if (log.action === 'EVENT_CREATED') {
            description = `created the event "${log.details.title || event.title}"`;
          } else if (log.action === 'PARTICIPANT_ADDED') {
            description = `added "${log.details.name}" to the event`;
          } else if (log.action === 'EXPENSE_CREATED') {
            description = `logged "${log.details.description}" (${log.details.currency || 'EUR'} ${log.details.amount})`;
          } else if (log.action === 'EXPENSE_UPDATED') {
            description = `updated "${log.details.description}"`;
          } else if (log.action === 'EXPENSE_DELETED') {
            description = `deleted expense "${log.details.description}"`;
          } else if (log.action === 'SETTLEMENT_RECORDED') {
            const toP = event.participants.find((p) => p.id === log.details.toParticipantId);
            description = `settled debt with ${toP?.name || 'someone'} (${event.baseCurrency} ${log.details.amount})`;
          }

          return (
            <div key={log.id} className="card-item" style={{ alignItems: 'flex-start', padding: '12px 14px' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <Avatar name={actor?.name || 'System'} color={actor?.avatarColor || '#6B7280'} size={32} />
                <div>
                  <div style={{ fontSize: '0.88rem', lineHeight: 1.4 }}>
                    <strong style={{ color: 'var(--text-primary)' }}>{actor?.name || 'System'}</strong>{' '}
                    <span style={{ color: 'var(--text-secondary)' }}>{description}</span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {formatRelativeTime(log.createdAt)}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
