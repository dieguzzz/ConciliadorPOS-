import React, { useState } from 'react';
import { FaFileExport, FaFileExcel, FaFileCsv, FaSpinner } from 'react-icons/fa';
import { Button, Modal } from './ui';
import { getApiBase } from '../utils/api';
import { notify } from '../utils/notifications';

interface ExportButtonProps {
  cierreData?: any;
  yappyData?: any;
  bancoData?: any;
  conciliacionYappy?: any[];
  conciliacionBanco?: any[];
  variant?: 'primary' | 'secondary' | 'outline';
}

export const ExportButton: React.FC<ExportButtonProps> = ({
  cierreData,
  yappyData,
  bancoData,
  conciliacionYappy,
  conciliacionBanco,
  variant = 'primary'
}) => {
  const [loading, setLoading] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  const handleExport = async (format: 'excel' | 'csv') => {
    setLoading(format);
    try {
      const apiBase = getApiBase();
      
      if (format === 'excel') {
        const response = await fetch(`${apiBase}/api/export/excel`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            cierre_data: cierreData,
            yappy_data: yappyData,
            banco_data: bancoData,
            conciliacion_yappy: conciliacionYappy,
            conciliacion_banco: conciliacionBanco
          })
        });

        if (!response.ok) {
          throw new Error('Error al exportar');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conciliacion_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        notify.success('Archivo Excel exportado correctamente');
      } else if (format === 'csv') {
        // Para CSV, exportar cada conjunto de datos por separado
        const datasets = [
          { name: 'conciliacion_yappy', data: conciliacionYappy },
          { name: 'conciliacion_banco', data: conciliacionBanco }
        ];

        for (const dataset of datasets) {
          if (dataset.data && dataset.data.length > 0) {
            const response = await fetch(`${apiBase}/api/export/csv`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                data: dataset.data,
                filename: `${dataset.name}_${new Date().toISOString().split('T')[0]}.csv`
              })
            });

            if (response.ok) {
              const blob = await response.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${dataset.name}_${new Date().toISOString().split('T')[0]}.csv`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);
            }
          }
        }
        
        notify.success('Archivos CSV exportados correctamente');
      }
      
      setShowModal(false);
    } catch (error: any) {
      notify.error(`Error al exportar: ${error.message}`);
    } finally {
      setLoading(null);
    }
  };

  const hasData = cierreData || yappyData || bancoData || 
                  (conciliacionYappy && conciliacionYappy.length > 0) ||
                  (conciliacionBanco && conciliacionBanco.length > 0);

  if (!hasData) {
    return null;
  }

  return (
    <>
      <Button
        variant={variant}
        onClick={() => setShowModal(true)}
      >
        <FaFileExport style={{ marginRight: '0.5rem' }} />
        Exportar
      </Button>

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Exportar Datos"
        size="sm"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Button
            variant="primary"
            fullWidth
            onClick={() => handleExport('excel')}
            loading={loading === 'excel'}
            disabled={loading !== null}
          >
            <FaFileExcel style={{ marginRight: '0.5rem' }} />
            Exportar a Excel
          </Button>

          <Button
            variant="outline"
            fullWidth
            onClick={() => handleExport('csv')}
            loading={loading === 'csv'}
            disabled={loading !== null}
          >
            <FaFileCsv style={{ marginRight: '0.5rem' }} />
            Exportar a CSV
          </Button>
        </div>
      </Modal>
    </>
  );
};

