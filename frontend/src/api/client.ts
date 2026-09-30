import { ENV } from '@/config/env';

/** Ошибка API с человекочитаемым объяснением и подсказкой по исправлению. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly hint: string,
    public readonly path: string,
  ) {
    super(message);
  }
}

function hintFor(status: number): string {
  if (status === 0) return 'Backend недоступен. Проверьте, что FastAPI запущен (uvicorn backend.app.main:app) и адрес VITE_API_BASE / прокси указан верно.';
  if (status === 401 || status === 403) return 'Нет доступа. Проверьте авторизацию backend и права API-ключа биржи.';
  if (status === 404) return 'Эндпоинт не найден. Backend ещё не реализует этот маршрут — см. раздел «Подключение backend» в README.';
  if (status === 408) return 'Сервер не ответил вовремя. Проверьте сеть или увеличьте VITE_API_TIMEOUT_MS.';
  if (status === 409) return 'Операция конфликтует с текущим состоянием (например, позиция уже закрыта). Обновите данные.';
  if (status === 422) return 'Backend отклонил параметры запроса. Проверьте значения полей.';
  if (status === 429) return 'Превышен лимит запросов биржи. Подождите несколько секунд.';
  if (status >= 500) return 'Внутренняя ошибка backend. Подробности — в журнале сервера.';
  return 'Повторите действие; если ошибка сохраняется — проверьте журнал.';
}

async function request<T>(method: string, path: string, body?: unknown, timeoutMs = ENV.apiTimeoutMs): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(ENV.apiBase + path, {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
  } catch (e) {
    const aborted = (e as Error).name === 'AbortError';
    throw new ApiError(aborted ? `Таймаут запроса ${path}` : `Нет соединения с ${path}`, aborted ? 408 : 0, hintFor(aborted ? 408 : 0), path);
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j?.detail === 'string' ? j.detail : JSON.stringify(j?.detail ?? j);
    } catch { /* тело не JSON */ }
    throw new ApiError(`${method} ${path}: ${res.status} ${detail}`, res.status, hintFor(res.status), path);
  }
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(`Некорректный JSON в ответе ${path}`, res.status, 'Backend вернул повреждённые данные.', path);
  }
}

export const http = {
  get: <T>(path: string, timeoutMs?: number) => request<T>('GET', path, undefined, timeoutMs),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body ?? {}),
};
