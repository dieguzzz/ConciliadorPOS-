import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  variant?: 'primary' | 'success' | 'warning' | 'danger';
  className?: string;
  style?: React.CSSProperties;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  showPercentage = true,
  variant = 'primary',
  className = '',
  style = {}
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  const getVariantColor = (): string => {
    const colors = {
      primary: '#6b5b95',
      success: '#28a745',
      warning: '#ffc107',
      danger: '#dc3545'
    };
    return colors[variant];
  };

  const baseStyle: React.CSSProperties = {
    width: '100%',
    ...style
  };

  const barStyle: React.CSSProperties = {
    width: '100%',
    height: '8px',
    backgroundColor: '#e9ecef',
    borderRadius: '4px',
    overflow: 'hidden',
    position: 'relative'
  };

  const fillStyle: React.CSSProperties = {
    height: '100%',
    width: `${clampedProgress}%`,
    backgroundColor: getVariantColor(),
    transition: 'width 0.3s ease',
    borderRadius: '4px'
  };

  return (
    <div className={className} style={baseStyle}>
      {(label || showPercentage) && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: '0.5rem',
          fontSize: '0.875rem',
          color: '#666'
        }}>
          {label && <span>{label}</span>}
          {showPercentage && <span>{Math.round(clampedProgress)}%</span>}
        </div>
      )}
      <div style={barStyle}>
        <div style={fillStyle} />
      </div>
    </div>
  );
};

