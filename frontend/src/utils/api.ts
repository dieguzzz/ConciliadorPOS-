/**
 * Obtiene la URL base del API automáticamente basándose en la URL actual del navegador.
 * 
 * Si hay una variable de entorno NEXT_PUBLIC_API_BASE, la usa (para producción).
 * Si no, detecta automáticamente la URL del backend basándose en la URL actual:
 * - Si accedes desde localhost:3000 → usa http://localhost:8000
 * - Si accedes desde 192.168.32.143:3000 → usa http://192.168.32.143:8000
 */
export function getApiBase(): string {
  // Si hay una variable de entorno configurada, usarla (para producción en Render)
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }

  // Si estamos en el navegador, detectar automáticamente la URL base
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // Si es localhost, usar localhost:8000
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    
    // Si es una IP de red local, usar la misma IP con puerto 8000 (siempre http en desarrollo)
    return `http://${hostname}:8000`;
  }

  // Fallback para SSR (server-side rendering)
  return 'http://localhost:8000';
}

