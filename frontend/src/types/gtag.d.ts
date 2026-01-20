/**
 * Type definitions for Google Analytics gtag function
 */
interface Window {
  dataLayer: any[];
  gtag: (
    command: 'config' | 'set' | 'event' | 'js' | 'get' | 'consent',
    targetId: string | Date,
    config?: Record<string, any>
  ) => void;
}

declare const gtag: (
  command: 'config' | 'set' | 'event' | 'js' | 'get' | 'consent',
  targetId: string | Date,
  config?: Record<string, any>
) => void;

