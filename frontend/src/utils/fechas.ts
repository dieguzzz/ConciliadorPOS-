/**
 * Utilidades para formatear fechas en español
 */

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

const DIAS_SEMANA = [
  "Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"
];

/**
 * Convierte una fecha a formato: "10 de Noviembre del 2025"
 */
export function fechaATexto(fecha: string | Date | null | undefined): string {
  if (!fecha) return "—";
  
  try {
    let fechaObj: Date;
    
    if (fecha instanceof Date) {
      fechaObj = fecha;
    } else if (typeof fecha === 'string') {
      // Intentar parsear diferentes formatos
      if (fecha.includes('/')) {
        // Formato DD/MM/YYYY o MM/DD/YYYY
        const partes = fecha.split('/');
        if (partes.length === 3) {
          const [dia, mes, año] = partes;
          fechaObj = new Date(parseInt(año), parseInt(mes) - 1, parseInt(dia));
        } else {
          fechaObj = new Date(fecha);
        }
      } else if (fecha.includes('-')) {
        // Formato YYYY-MM-DD o similar
        fechaObj = new Date(fecha);
      } else {
        fechaObj = new Date(fecha);
      }
    } else {
      return "—";
    }
    
    if (isNaN(fechaObj.getTime())) {
      return fecha.toString();
    }
    
    const dia = fechaObj.getDate();
    const mes = MESES[fechaObj.getMonth()];
    const año = fechaObj.getFullYear();
    
    return `${dia} de ${mes} del ${año}`;
  } catch (error) {
    console.error("Error formateando fecha:", error);
    return fecha?.toString() || "—";
  }
}

/**
 * Convierte una fecha a formato con día de semana: "Lunes, 10 de Noviembre del 2025"
 */
export function fechaATextoCompleto(fecha: string | Date | null | undefined): string {
  if (!fecha) return "—";
  
  try {
    let fechaObj: Date;
    
    if (fecha instanceof Date) {
      fechaObj = fecha;
    } else {
      fechaObj = new Date(fecha);
    }
    
    if (isNaN(fechaObj.getTime())) {
      return fecha.toString();
    }
    
    const diaSemana = DIAS_SEMANA[fechaObj.getDay()];
    const dia = fechaObj.getDate();
    const mes = MESES[fechaObj.getMonth()];
    const año = fechaObj.getFullYear();
    
    return `${diaSemana}, ${dia} de ${mes} del ${año}`;
  } catch (error) {
    console.error("Error formateando fecha:", error);
    return fecha?.toString() || "—";
  }
}

/**
 * Convierte número a texto (ej: 1234.56 -> "Mil doscientos treinta y cuatro con 56/100")
 * Para montos en Balboas
 */
export function numeroATexto(numero: number): string {
  if (!numero && numero !== 0) return "—";
  
  const [entero, decimal] = numero.toFixed(2).split('.');
  const enteroNum = parseInt(entero);
  
  if (enteroNum === 0) {
    return `Cero Balboas con ${decimal}/100`;
  }
  
  const texto = numeroATextoHelper(enteroNum);
  return `${texto} Balboas con ${decimal}/100`;
}

function numeroATextoHelper(num: number): string {
  const unidades = ["", "Uno", "Dos", "Tres", "Cuatro", "Cinco", "Seis", "Siete", "Ocho", "Nueve"];
  const decenas = ["", "Diez", "Veinte", "Treinta", "Cuarenta", "Cincuenta", "Sesenta", "Setenta", "Ochenta", "Noventa"];
  const especiales = ["Diez", "Once", "Doce", "Trece", "Catorce", "Quince", "Dieciséis", "Diecisiete", "Dieciocho", "Diecinueve"];
  const centenas = ["", "Ciento", "Doscientos", "Trescientos", "Cuatrocientos", "Quinientos", "Seiscientos", "Setecientos", "Ochocientos", "Novecientos"];
  
  if (num === 0) return "Cero";
  if (num < 10) return unidades[num];
  if (num >= 10 && num < 20) return especiales[num - 10];
  if (num >= 20 && num < 100) {
    const dec = Math.floor(num / 10);
    const uni = num % 10;
    return uni === 0 ? decenas[dec] : `${decenas[dec]} y ${unidades[uni]}`;
  }
  if (num >= 100 && num < 1000) {
    const cen = Math.floor(num / 100);
    const resto = num % 100;
    const cenText = num === 100 ? "Cien" : centenas[cen];
    return resto === 0 ? cenText : `${cenText} ${numeroATextoHelper(resto)}`;
  }
  if (num >= 1000 && num < 1000000) {
    const mil = Math.floor(num / 1000);
    const resto = num % 1000;
    const milText = mil === 1 ? "Mil" : `${numeroATextoHelper(mil)} Mil`;
    return resto === 0 ? milText : `${milText} ${numeroATextoHelper(resto)}`;
  }
  
  return num.toString(); // Fallback para números muy grandes
}

/**
 * Formatea monto con texto (ej: "B/. 1,234.56 (Mil doscientos treinta y cuatro Balboas con 56/100)")
 */
export function formatearMontoConTexto(monto: number): string {
  const montoFormateado = `B/. ${monto.toLocaleString('es-PA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const montoTexto = numeroATexto(monto);
  return `${montoFormateado} (${montoTexto})`;
}

