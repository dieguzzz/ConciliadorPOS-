import React, { useState } from 'react';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';

type SortDirection = 'asc' | 'desc' | null;

interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
  pagination?: {
    pageSize: number;
    showPagination?: boolean;
  };
  className?: string;
  style?: React.CSSProperties;
  emptyMessage?: string;
}

export function Table<T extends Record<string, any>>({
  data,
  columns,
  onRowClick,
  pagination,
  className = '',
  style = {},
  emptyMessage = 'No hay datos disponibles'
}: TableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const handleSort = (columnKey: string) => {
    const column = columns.find(col => col.key === columnKey);
    if (!column?.sortable) return;

    if (sortColumn === columnKey) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortColumn(null);
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortColumn || !sortDirection) return 0;

    const aVal = a[sortColumn];
    const bVal = b[sortColumn];

    if (aVal === bVal) return 0;

    const comparison = aVal < bVal ? -1 : 1;
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const pageSize = pagination?.pageSize || 10;
  const showPagination = pagination?.showPagination !== false;
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedData = showPagination
    ? sortedData.slice(startIndex, startIndex + pageSize)
    : sortedData;

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) {
      return <FaSort style={{ opacity: 0.3 }} />;
    }
    return sortDirection === 'asc' ? <FaSortUp /> : <FaSortDown />;
  };

  if (data.length === 0) {
    return (
      <div
        style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#666',
          ...style
        }}
        className={className}
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={className} style={style}>
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            overflow: 'hidden'
          }}
        >
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
              {columns.map((column) => (
                <th
                  key={column.key}
                  onClick={() => handleSort(column.key)}
                  style={{
                    padding: '0.75rem 1rem',
                    textAlign: column.align || 'left',
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    color: '#495057',
                    cursor: column.sortable ? 'pointer' : 'default',
                    userSelect: 'none',
                    width: column.width,
                    position: 'relative'
                  }}
                  onMouseEnter={(e) => {
                    if (column.sortable) {
                      e.currentTarget.style.backgroundColor = '#e9ecef';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (column.sortable) {
                      e.currentTarget.style.backgroundColor = '#f8f9fa';
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>{column.label}</span>
                    {column.sortable && (
                      <span style={{ fontSize: '0.75rem' }}>
                        {getSortIcon(column.key)}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, index) => (
              <tr
                key={index}
                onClick={() => onRowClick?.(row)}
                style={{
                  borderBottom: '1px solid #dee2e6',
                  cursor: onRowClick ? 'pointer' : 'default',
                  transition: 'background-color 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#ffffff';
                }}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    style={{
                      padding: '0.75rem 1rem',
                      textAlign: column.align || 'left',
                      fontSize: '0.875rem',
                      color: '#212529'
                    }}
                  >
                    {column.render
                      ? column.render(row[column.key], row)
                      : row[column.key] ?? '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showPagination && totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '1rem',
            padding: '0.75rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px'
          }}
        >
          <div style={{ fontSize: '0.875rem', color: '#666' }}>
            Mostrando {startIndex + 1} - {Math.min(startIndex + pageSize, sortedData.length)} de {sortedData.length}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              style={{
                padding: '0.375rem 0.75rem',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                background: currentPage === 1 ? '#f8f9fa' : '#ffffff',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                color: currentPage === 1 ? '#adb5bd' : '#495057'
              }}
            >
              Anterior
            </button>
            <span style={{ padding: '0.375rem 0.75rem', color: '#495057' }}>
              Página {currentPage} de {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              style={{
                padding: '0.375rem 0.75rem',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                background: currentPage === totalPages ? '#f8f9fa' : '#ffffff',
                cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                color: currentPage === totalPages ? '#adb5bd' : '#495057'
              }}
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

