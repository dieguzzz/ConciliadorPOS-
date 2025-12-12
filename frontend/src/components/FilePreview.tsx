import React from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaFileExcel, FaFileCsv } from 'react-icons/fa';
import { Card, CardHeader, CardBody, Alert } from './ui';
import { validateFile, getFileInfo, FileValidationResult } from '../utils/fileValidators';

interface FilePreviewProps {
  file: File | null;
  expectedType?: 'excel' | 'csv' | 'any';
  onRemove?: () => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  expectedType = 'any',
  onRemove
}) => {
  if (!file) {
    return null;
  }

  const validation: FileValidationResult = validateFile(file, expectedType);
  const fileInfo = getFileInfo(file);
  const isExcel = file.name.toLowerCase().endsWith('.xlsx') || 
                  file.name.toLowerCase().endsWith('.xls') ||
                  file.name.toLowerCase().endsWith('.xlsm') ||
                  file.name.toLowerCase().endsWith('.xlsb') ||
                  file.name.toLowerCase().endsWith('.ods');
  const isCsv = file.name.toLowerCase().endsWith('.csv');

  return (
    <Card style={{ marginTop: '1rem' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {isExcel && <FaFileExcel style={{ color: '#28a745' }} />}
            {isCsv && <FaFileCsv style={{ color: '#17a2b8' }} />}
            <span>Vista Previa del Archivo</span>
          </div>
          {onRemove && (
            <button
              onClick={onRemove}
              style={{
                background: 'none',
                border: 'none',
                color: '#dc3545',
                cursor: 'pointer',
                fontSize: '1.25rem',
                padding: '0.25rem 0.5rem'
              }}
            >
              ×
            </button>
          )}
        </div>
      </CardHeader>
      <CardBody>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem',
            marginBottom: '0.5rem'
          }}>
            {validation.valid ? (
              <FaCheckCircle style={{ color: '#28a745' }} />
            ) : (
              <FaExclamationTriangle style={{ color: '#dc3545' }} />
            )}
            <strong>{fileInfo.name}</strong>
          </div>
          
          <div style={{ 
            fontSize: '0.875rem', 
            color: '#6c757d',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '0.5rem',
            marginTop: '0.5rem'
          }}>
            <div>
              <strong>Tamaño:</strong> {fileInfo.size}
            </div>
            <div>
              <strong>Tipo:</strong> {fileInfo.type}
            </div>
            <div>
              <strong>Modificado:</strong> {fileInfo.lastModified}
            </div>
          </div>
        </div>

        {!validation.valid && (
          <Alert variant="error" title="Errores de validación">
            <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
              {validation.errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          </Alert>
        )}

        {validation.warnings.length > 0 && (
          <Alert variant="warning" title="Advertencias">
            <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
              {validation.warnings.map((warning, idx) => (
                <li key={idx}>{warning}</li>
              ))}
            </ul>
          </Alert>
        )}

        {validation.valid && validation.warnings.length === 0 && (
          <Alert variant="success">
            El archivo es válido y está listo para procesar
          </Alert>
        )}
      </CardBody>
    </Card>
  );
};

