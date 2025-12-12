import React from 'react';
import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimesCircle } from 'react-icons/fa';

type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  children: React.ReactNode;
  variant?: AlertVariant;
  title?: string;
  onClose?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'info',
  title,
  onClose,
  className = '',
  style = {}
}) => {
  const getVariantStyles = (): { bg: string; border: string; icon: React.ReactNode; color: string } => {
    const variants = {
      success: {
        bg: '#d4edda',
        border: '#c3e6cb',
        icon: <FaCheckCircle />,
        color: '#155724'
      },
      error: {
        bg: '#f8d7da',
        border: '#f5c6cb',
        icon: <FaTimesCircle />,
        color: '#721c24'
      },
      warning: {
        bg: '#fff3cd',
        border: '#ffeaa7',
        icon: <FaExclamationCircle />,
        color: '#856404'
      },
      info: {
        bg: '#d1ecf1',
        border: '#bee5eb',
        icon: <FaInfoCircle />,
        color: '#0c5460'
      }
    };
    return variants[variant];
  };

  const variantStyles = getVariantStyles();

  const baseStyle: React.CSSProperties = {
    padding: '1rem',
    borderRadius: '6px',
    border: `1px solid ${variantStyles.border}`,
    backgroundColor: variantStyles.bg,
    color: variantStyles.color,
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.75rem',
    ...style
  };

  return (
    <div className={className} style={baseStyle}>
      <div style={{ fontSize: '1.25rem', flexShrink: 0, marginTop: '0.125rem' }}>
        {variantStyles.icon}
      </div>
      <div style={{ flex: 1 }}>
        {title && (
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
            {title}
          </div>
        )}
        <div>{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: variantStyles.color,
            cursor: 'pointer',
            fontSize: '1.25rem',
            padding: 0,
            marginLeft: '0.5rem',
            opacity: 0.7,
            flexShrink: 0
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '1';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = '0.7';
          }}
        >
          ×
        </button>
      )}
    </div>
  );
};

