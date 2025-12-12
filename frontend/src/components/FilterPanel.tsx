import React, { useState } from 'react';
import { FaFilter, FaTimes, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import { Card, CardHeader, CardBody, Button } from './ui';

export interface Filter {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'range';
  value?: any;
  options?: { label: string; value: any }[];
  min?: number;
  max?: number;
}

interface FilterPanelProps {
  filters: Filter[];
  onFilterChange: (filters: Filter[]) => void;
  onClearAll?: () => void;
  title?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFilterChange,
  onClearAll,
  title = 'Filtros',
  collapsible = true,
  defaultCollapsed = false
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [localFilters, setLocalFilters] = useState<Filter[]>(filters);

  const activeFiltersCount = localFilters.filter(f => {
    if (f.type === 'text') return f.value && f.value.trim() !== '';
    if (f.type === 'number' || f.type === 'range') return f.value !== undefined && f.value !== '';
    if (f.type === 'date') return f.value !== undefined && f.value !== '';
    if (f.type === 'select') return f.value !== undefined && f.value !== '';
    return false;
  }).length;

  const handleFilterChange = (key: string, value: any) => {
    const updated = localFilters.map(f => 
      f.key === key ? { ...f, value } : f
    );
    setLocalFilters(updated);
    onFilterChange(updated);
  };

  const handleClearAll = () => {
    const cleared = localFilters.map(f => ({ ...f, value: undefined }));
    setLocalFilters(cleared);
    onFilterChange(cleared);
    onClearAll?.();
  };

  const renderFilterInput = (filter: Filter) => {
    switch (filter.type) {
      case 'text':
        return (
          <input
            type="text"
            value={filter.value || ''}
            onChange={(e) => handleFilterChange(filter.key, e.target.value)}
            placeholder={`Buscar ${filter.label.toLowerCase()}...`}
            style={{
              width: '100%',
              padding: '0.5rem',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              fontSize: '0.875rem'
            }}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={filter.value || ''}
            onChange={(e) => handleFilterChange(filter.key, e.target.value ? parseFloat(e.target.value) : undefined)}
            placeholder={filter.label}
            min={filter.min}
            max={filter.max}
            style={{
              width: '100%',
              padding: '0.5rem',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              fontSize: '0.875rem'
            }}
          />
        );

      case 'range':
        return (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <input
              type="number"
              value={filter.value?.min || ''}
              onChange={(e) => handleFilterChange(filter.key, {
                ...filter.value,
                min: e.target.value ? parseFloat(e.target.value) : undefined
              })}
              placeholder="Mín"
              min={filter.min}
              style={{
                flex: 1,
                padding: '0.5rem',
                borderRadius: '6px',
                border: '1px solid #dee2e6',
                fontSize: '0.875rem'
              }}
            />
            <span>-</span>
            <input
              type="number"
              value={filter.value?.max || ''}
              onChange={(e) => handleFilterChange(filter.key, {
                ...filter.value,
                max: e.target.value ? parseFloat(e.target.value) : undefined
              })}
              placeholder="Máx"
              max={filter.max}
              style={{
                flex: 1,
                padding: '0.5rem',
                borderRadius: '6px',
                border: '1px solid #dee2e6',
                fontSize: '0.875rem'
              }}
            />
          </div>
        );

      case 'date':
        return (
          <input
            type="date"
            value={filter.value || ''}
            onChange={(e) => handleFilterChange(filter.key, e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              fontSize: '0.875rem'
            }}
          />
        );

      case 'select':
        return (
          <select
            value={filter.value || ''}
            onChange={(e) => handleFilterChange(filter.key, e.target.value || undefined)}
            style={{
              width: '100%',
              padding: '0.5rem',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              fontSize: '0.875rem',
              background: '#fff'
            }}
          >
            <option value="">Todos</option>
            {filter.options?.map((opt, idx) => (
              <option key={idx} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      default:
        return null;
    }
  };

  const content = (
    <CardBody>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '1rem'
      }}>
        {localFilters.map((filter) => (
          <div key={filter.key}>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: '#495057'
            }}>
              {filter.label}
            </label>
            {renderFilterInput(filter)}
          </div>
        ))}
      </div>

      {activeFiltersCount > 0 && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          paddingTop: '1rem',
          borderTop: '1px solid #dee2e6'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>
            {activeFiltersCount} filtro{activeFiltersCount !== 1 ? 's' : ''} activo{activeFiltersCount !== 1 ? 's' : ''}
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleClearAll}
          >
            <FaTimes style={{ marginRight: '0.25rem' }} />
            Limpiar todos
          </Button>
        </div>
      )}
    </CardBody>
  );

  if (!collapsible) {
    return (
      <Card>
        <CardHeader>
          <FaFilter style={{ marginRight: '0.5rem', display: 'inline' }} />
          {title}
          {activeFiltersCount > 0 && (
            <span style={{ 
              marginLeft: '0.5rem',
              background: '#6b5b95',
              color: '#fff',
              borderRadius: '12px',
              padding: '0.125rem 0.5rem',
              fontSize: '0.75rem'
            }}>
              {activeFiltersCount}
            </span>
          )}
        </CardHeader>
        {content}
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            cursor: 'pointer'
          }}
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FaFilter />
            <span>{title}</span>
            {activeFiltersCount > 0 && (
              <span style={{ 
                background: '#6b5b95',
                color: '#fff',
                borderRadius: '12px',
                padding: '0.125rem 0.5rem',
                fontSize: '0.75rem'
              }}>
                {activeFiltersCount}
              </span>
            )}
          </div>
          {isCollapsed ? <FaChevronDown /> : <FaChevronUp />}
        </div>
      </CardHeader>
      {!isCollapsed && content}
    </Card>
  );
};

