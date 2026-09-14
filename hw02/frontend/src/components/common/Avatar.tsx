import React from 'react';

interface AvatarProps {
  name: string;
  color?: string;
  size?: number;
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
  name,
  color = '#6366F1',
  size = 36,
  className = '',
}) => {
  const initial = (name || '?').charAt(0).toUpperCase();

  return (
    <div
      className={`avatar ${className}`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: color,
        fontSize: `${Math.round(size * 0.42)}px`,
      }}
      title={name}
      aria-label={name}
    >
      {initial}
    </div>
  );
};
