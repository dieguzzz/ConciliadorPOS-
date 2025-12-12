import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  style = {},
  onClick,
  hover = false 
}) => {
  const baseStyle: React.CSSProperties = {
    background: '#ffffff',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    padding: '1.5rem',
    transition: 'all 0.2s ease',
    ...(hover && {
      cursor: onClick ? 'pointer' : 'default',
      ':hover': {
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.15)',
        transform: 'translateY(-2px)'
      }
    }),
    ...style
  };

  return (
    <div 
      className={className}
      style={baseStyle}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (hover && onClick) {
          e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.15)';
          e.currentTarget.style.transform = 'translateY(-2px)';
        }
      }}
      onMouseLeave={(e) => {
        if (hover) {
          e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
          e.currentTarget.style.transform = 'translateY(0)';
        }
      }}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ 
  children, 
  className = '', 
  style = {} 
}) => {
  return (
    <div 
      className={className}
      style={{
        fontSize: '1.1rem',
        fontWeight: 600,
        marginBottom: '1rem',
        color: '#333',
        borderBottom: '1px solid #e0e0e0',
        paddingBottom: '0.75rem',
        ...style
      }}
    >
      {children}
    </div>
  );
};

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const CardBody: React.FC<CardBodyProps> = ({ 
  children, 
  className = '', 
  style = {} 
}) => {
  return (
    <div 
      className={className}
      style={{
        ...style
      }}
    >
      {children}
    </div>
  );
};

