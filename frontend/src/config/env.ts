/** Конфигурация сборки. Только публичные значения — секретов во фронтенде нет. */
export type DataModeSetting = 'auto' | 'live' | 'demo';

const raw = import.meta.env;

function num(v: string | undefined, d: number) {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : d;
}

export const ENV = {
  dataMode: (['auto', 'live', 'demo'].includes(raw.VITE_DATA_MODE) ? raw.VITE_DATA_MODE : 'auto') as DataModeSetting,
  apiBase: (raw.VITE_API_BASE || '').replace(/\/$/, ''),
  wsBase: (raw.VITE_WS_BASE || '').replace(/\/$/, ''),
  apiTimeoutMs: num(raw.VITE_API_TIMEOUT_MS, 8000),
  staleAfterSec: num(raw.VITE_STALE_AFTER_SEC, 15),
};

export function wsUrl(path: string): string {
  if (ENV.wsBase) return ENV.wsBase + path;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${location.host}${path}`;
}
