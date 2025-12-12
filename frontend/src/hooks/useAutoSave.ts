import { useEffect, useRef } from 'react';

export function useAutoSave<T>(
  data: T,
  key: string,
  interval: number = 30000 // 30 segundos por defecto
) {
  const dataRef = useRef<T>(data);
  const lastSaveRef = useRef<Date>(new Date());

  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  useEffect(() => {
    const save = () => {
      try {
        localStorage.setItem(key, JSON.stringify(dataRef.current));
        lastSaveRef.current = new Date();
      } catch (error) {
        console.error('Error guardando en localStorage:', error);
      }
    };

    // Guardar inmediatamente cuando cambian los datos
    save();

    // Guardar periódicamente
    const intervalId = setInterval(save, interval);

    // Guardar antes de cerrar la página
    const handleBeforeUnload = () => {
      save();
    };
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [key, interval]);

  const load = (): T | null => {
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.error('Error cargando de localStorage:', error);
    }
    return null;
  };

  const clear = () => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error limpiando localStorage:', error);
    }
  };

  return {
    load,
    clear,
    lastSave: lastSaveRef.current
  };
}

