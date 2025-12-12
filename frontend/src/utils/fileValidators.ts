/**
 * Utilidades para validar archivos antes de subirlos
 */

export interface FileValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_EXCEL_EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.xlsb', '.ods'];
const ALLOWED_CSV_EXTENSIONS = ['.csv'];

export function validateFile(file: File, expectedType: 'excel' | 'csv' | 'any' = 'any'): FileValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Validar tamaño
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`El archivo es demasiado grande. Tamaño máximo: ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)}MB`);
  }

  if (file.size === 0) {
    errors.push('El archivo está vacío');
  }

  // Validar extensión
  const fileName = file.name.toLowerCase();
  const extension = fileName.substring(fileName.lastIndexOf('.'));

  if (expectedType === 'excel') {
    if (!ALLOWED_EXCEL_EXTENSIONS.includes(extension)) {
      errors.push(`Extensión no válida. Extensiones permitidas: ${ALLOWED_EXCEL_EXTENSIONS.join(', ')}`);
    }
  } else if (expectedType === 'csv') {
    if (!ALLOWED_CSV_EXTENSIONS.includes(extension)) {
      errors.push(`Extensión no válida. Extensiones permitidas: ${ALLOWED_CSV_EXTENSIONS.join(', ')}`);
    }
  } else {
    const allAllowed = [...ALLOWED_EXCEL_EXTENSIONS, ...ALLOWED_CSV_EXTENSIONS];
    if (!allAllowed.includes(extension)) {
      errors.push(`Extensión no válida. Extensiones permitidas: ${allAllowed.join(', ')}`);
    }
  }

  // Advertencias
  if (file.size > 10 * 1024 * 1024) { // > 10MB
    warnings.push('El archivo es grande, el procesamiento puede tardar');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

export function validateExcelStructure(file: File): Promise<FileValidationResult> {
  return new Promise((resolve) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Para Excel, intentar leer con una librería del lado del cliente si está disponible
    // Por ahora, solo validamos la extensión y tamaño
    const validation = validateFile(file, 'excel');
    
    // Si hay errores de validación básica, retornarlos
    if (!validation.valid) {
      resolve(validation);
      return;
    }

    // Validaciones adicionales podrían ir aquí si tenemos acceso a leer el Excel en el cliente
    // Por ahora, asumimos que la estructura se validará en el backend
    
    resolve({
      valid: true,
      errors: [],
      warnings: validation.warnings
    });
  });
}

export function getFileInfo(file: File): {
  name: string;
  size: string;
  type: string;
  lastModified: string;
} {
  return {
    name: file.name,
    size: formatFileSize(file.size),
    type: file.type || 'Desconocido',
    lastModified: new Date(file.lastModified).toLocaleString('es-PA')
  };
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

