import React, { useState, useEffect } from 'react';
import { FaHistory, FaEye, FaTrash, FaSearch } from 'react-icons/fa';
import { Card, CardHeader, CardBody, Table, Button, Modal, FilterPanel, Filter } from './ui';
import { getApiBase } from '../utils/api';
import { notify } from '../utils/notifications';

interface ConciliacionItem {
  id: number;
  fecha_conciliacion: string;
  fecha_cierre: string;
  sucursal: string;
  cajero: string;
  estado: string;
  total_coincidencias_exactas: number;
  total_coincidencias_parciales: number;
  total_sin_coincidencia: number;
  created_at: string;
}

export const Historial: React.FC = () => {
  const [conciliaciones, setConciliaciones] = useState<ConciliacionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(10);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [details, setDetails] = useState<any>(null);
  
  const [filters, setFilters] = useState<Filter[]>([
    { key: 'fecha_inicio', label: 'Fecha Inicio', type: 'date' },
    { key: 'fecha_fin', label: 'Fecha Fin', type: 'date' },
    { key: 'sucursal', label: 'Sucursal', type: 'text' },
    { 
      key: 'estado', 
      label: 'Estado', 
      type: 'select',
      options: [
        { label: 'Completa', value: 'completa' },
        { label: 'Parcial', value: 'parcial' },
        { label: 'Con Errores', value: 'con_errores' }
      ]
    }
  ]);

  useEffect(() => {
    loadHistorial();
  }, [skip, filters]);

  const loadHistorial = async () => {
    setLoading(true);
    try {
      const apiBase = getApiBase();
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: limit.toString()
      });

      filters.forEach(filter => {
        if (filter.value) {
          if (filter.type === 'date') {
            const date = new Date(filter.value);
            params.append(filter.key, date.toISOString().split('T')[0]);
          } else {
            params.append(filter.key, filter.value.toString());
          }
        }
      });

      const response = await fetch(`${apiBase}/api/historial?${params}`);
      const json = await response.json();

      if (json.success && json.data) {
        setConciliaciones(json.data.conciliaciones || []);
        setTotal(json.data.total || 0);
      } else {
        notify.error(json.message || 'Error al cargar historial');
      }
    } catch (error: any) {
      notify.error(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (id: number) => {
    try {
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/api/historial/${id}`);
      const json = await response.json();

      if (json.success && json.data) {
        setDetails(json.data);
        setSelectedId(id);
        setShowDetails(true);
      } else {
        notify.error('Error al cargar detalles');
      }
    } catch (error: any) {
      notify.error(`Error: ${error.message}`);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar esta conciliación?')) {
      return;
    }

    try {
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/api/historial/${id}`, {
        method: 'DELETE'
      });
      const json = await response.json();

      if (json.success) {
        notify.success('Conciliación eliminada correctamente');
        loadHistorial();
      } else {
        notify.error(json.message || 'Error al eliminar');
      }
    } catch (error: any) {
      notify.error(`Error: ${error.message}`);
    }
  };

  const columns = [
    {
      key: 'fecha_conciliacion',
      label: 'Fecha',
      sortable: true,
      render: (value: string) => {
        if (!value) return '—';
        const date = new Date(value);
        return date.toLocaleDateString('es-PA');
      }
    },
    {
      key: 'sucursal',
      label: 'Sucursal',
      sortable: true
    },
    {
      key: 'cajero',
      label: 'Cajero',
      sortable: true
    },
    {
      key: 'estado',
      label: 'Estado',
      sortable: true,
      render: (value: string) => {
        const estados: Record<string, { label: string; color: string }> = {
          completa: { label: 'Completa', color: '#28a745' },
          parcial: { label: 'Parcial', color: '#ffc107' },
          con_errores: { label: 'Con Errores', color: '#dc3545' }
        };
        const estado = estados[value] || { label: value, color: '#6c757d' };
        return (
          <span style={{ 
            color: estado.color, 
            fontWeight: 600,
            fontSize: '0.875rem'
          }}>
            {estado.label}
          </span>
        );
      }
    },
    {
      key: 'total_coincidencias_exactas',
      label: 'Exactas',
      sortable: true,
      align: 'right' as const
    },
    {
      key: 'total_coincidencias_parciales',
      label: 'Parciales',
      sortable: true,
      align: 'right' as const
    },
    {
      key: 'actions',
      label: 'Acciones',
      render: (_: any, row: ConciliacionItem) => (
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleViewDetails(row.id)}
          >
            <FaEye />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDelete(row.id)}
          >
            <FaTrash style={{ color: '#dc3545' }} />
          </Button>
        </div>
      )
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FaHistory />
            <span>Historial de Conciliaciones</span>
          </div>
        </CardHeader>
        <CardBody>
          <FilterPanel
            filters={filters}
            onFilterChange={setFilters}
            onClearAll={() => {
              const cleared = filters.map(f => ({ ...f, value: undefined }));
              setFilters(cleared);
              setSkip(0);
            }}
            title="Filtros"
          />

          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              Cargando...
            </div>
          ) : (
            <>
              <Table
                data={conciliaciones}
                columns={columns}
                pagination={{
                  pageSize: limit,
                  showPagination: total > limit
                }}
                emptyMessage="No hay conciliaciones en el historial"
              />

              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginTop: '1rem'
              }}>
                <div style={{ fontSize: '0.875rem', color: '#6c757d' }}>
                  Mostrando {skip + 1} - {Math.min(skip + limit, total)} de {total}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSkip(Math.max(0, skip - limit))}
                    disabled={skip === 0}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSkip(skip + limit)}
                    disabled={skip + limit >= total}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardBody>
      </Card>

      <Modal
        isOpen={showDetails}
        onClose={() => setShowDetails(false)}
        title="Detalles de Conciliación"
        size="lg"
      >
        {details && (
          <div>
            <pre style={{ 
              background: '#f8f9fa', 
              padding: '1rem', 
              borderRadius: '6px',
              overflow: 'auto',
              maxHeight: '500px',
              fontSize: '0.875rem'
            }}>
              {JSON.stringify(details, null, 2)}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  );
};

