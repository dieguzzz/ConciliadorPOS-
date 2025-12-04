
export function getApiBase(): string {
  // Prioridad: variable pública definida en build
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }

  // Desarrollo local
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;

    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }

    // Hardcodear la URL del backend (no es ideal pero funciona)
    return "https://conciliador-backend-production.up.railway.app";
  }

  return "http://localhost:8000";
}


