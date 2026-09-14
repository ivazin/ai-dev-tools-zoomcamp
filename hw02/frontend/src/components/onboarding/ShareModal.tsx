import React, { useEffect, useRef, useState } from 'react';
import QRCode from 'qrcode';
import { Modal } from '../common/Modal';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  eventTitle: string;
}

export const ShareModal: React.FC<ShareModalProps> = ({ isOpen, onClose, eventTitle }) => {
  const [copied, setCopied] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const shareUrl = window.location.href;

  useEffect(() => {
    if (isOpen && canvasRef.current) {
      QRCode.toCanvas(canvasRef.current, shareUrl, {
        width: 200,
        margin: 1,
        color: {
          dark: '#000000',
          light: '#ffffff',
        },
      }).catch((err) => {
        console.error('Failed to generate QR code', err);
      });
    }
  }, [isOpen, shareUrl]);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
    }
  };

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: eventTitle,
          text: `Join "${eventTitle}" on SplitWave to split expenses!`,
          url: shareUrl,
        });
      } catch {
        // User dismissed
      }
    } else {
      handleCopyLink();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Share Event">
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center' }}>
          Scan this QR code with a phone camera or copy the link to share with your group.
        </p>

        {/* QR Code Container */}
        <div
          style={{
            background: '#ffffff',
            padding: '12px',
            borderRadius: '16px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <canvas ref={canvasRef} />
        </div>

        {/* Share Link Row */}
        <div style={{ width: '100%', display: 'flex', gap: '8px' }}>
          <input
            type="text"
            readOnly
            value={shareUrl}
            style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}
          />
          <button
            className="btn-secondary"
            onClick={handleCopyLink}
            style={{ flex: 'none', padding: '10px 16px', minWidth: '90px' }}
          >
            {copied ? 'Copied ✓' : 'Copy'}
          </button>
        </div>

        {/* Native Share button */}
        {'share' in navigator && (
          <button
            className="btn-primary"
            onClick={handleNativeShare}
            style={{ width: '100%' }}
          >
            Open Native Share Sheet
          </button>
        )}
      </div>
    </Modal>
  );
};
