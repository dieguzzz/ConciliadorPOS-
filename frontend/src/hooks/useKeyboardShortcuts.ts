import { useEffect } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      shortcuts.forEach((shortcut) => {
        const ctrlMatch = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          event.preventDefault();
          shortcut.action();
        }
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts]);
}

export const defaultShortcuts: KeyboardShortcut[] = [
  {
    key: 's',
    ctrl: true,
    action: () => {
      // Guardar conciliación
      console.log('Ctrl+S: Guardar');
    },
    description: 'Guardar conciliación'
  },
  {
    key: 'e',
    ctrl: true,
    action: () => {
      // Exportar
      console.log('Ctrl+E: Exportar');
    },
    description: 'Exportar datos'
  },
  {
    key: 'f',
    ctrl: true,
    action: () => {
      // Buscar
      const searchInput = document.querySelector('input[type="search"], input[placeholder*="buscar" i]') as HTMLInputElement;
      if (searchInput) {
        searchInput.focus();
      }
    },
    description: 'Buscar'
  },
  {
    key: 'Escape',
    action: () => {
      // Cerrar modales
      const modals = document.querySelectorAll('[role="dialog"], .modal');
      modals.forEach((modal: any) => {
        if (modal.style.display !== 'none') {
          const closeButton = modal.querySelector('button[aria-label*="close" i], button:has(> svg)');
          if (closeButton) {
            closeButton.click();
          }
        }
      });
    },
    description: 'Cerrar modales'
  }
];

