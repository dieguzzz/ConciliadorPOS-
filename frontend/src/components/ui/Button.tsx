import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'outline';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  style?: React.CSSProperties;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  type = 'button',
  className = '',
  style = {},
  fullWidth = false
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    const variants = {
      primary: {
        background: '#6b5b95',
        color: '#ffffff',
        border: '1px solid #6b5b95'
      },
      secondary: {
        background: '#6c757d',
        color: '#ffffff',
        border: '1px solid #6c757d'
      },
      success: {
        background: '#28a745',
        color: '#ffffff',
        border: '1px solid #28a745'
      },
      danger: {
        background: '#dc3545',
        color: '#ffffff',
        border: '1px solid #dc3545'
      },
      warning: {
        background: '#ffc107',
        color: '#212529',
        border: '1px solid #ffc107'
      },
      outline: {
        background: 'transparent',
        color: '#6b5b95',
        border: '1px solid #6b5b95'
      }
    };
    return variants[variant];
  };

  const getSizeStyles = (): React.CSSProperties => {
    const sizes = {
      sm: {
        padding: '0.375rem 0.75rem',
        fontSize: '0.875rem'
      },
      md: {
        padding: '0.5rem 1rem',
        fontSize: '1rem'
      },
      lg: {
        padding: '0.75rem 1.5rem',
        fontSize: '1.125rem'
      }
    };
    return sizes[size];
  };

  const baseStyle: React.CSSProperties = {
    ...getVariantStyles(),
    ...getSizeStyles(),
    borderRadius: '6px',
    fontWeight: 500,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.6 : 1,
    transition: 'all 0.2s ease',
    border: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    width: fullWidth ? '100%' : 'auto',
    ...style
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={className}
      style={baseStyle}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.opacity = '0.9';
          e.currentTarget.style.transform = 'translateY(-1px)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.opacity = '1';
          e.currentTarget.style.transform = 'translateY(0)';
        }
      }}
    >
      {loading && (
        <span style={{ 
          display: 'inline-block',
          width: '14px',
          height: '14px',
          border: '2px solid currentColor',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 0.6s linear infinite'
        }} />
      )}
      {children}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
};

