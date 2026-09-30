/**
 * REST-эндпоинты «Валькирии». Пути соответствуют контракту из ТЗ;
 * адаптеры приводят ответы к доменным типам. Если backend отдаёт
 * данные в другом формате — правьте адаптер, а не компоненты.
 */
import { http } from './client';
import * as A from './adapters';
import type { ClosePositionRequest, CommandResult, OpenOrderRequest, RiskSettings, StrategySettings, Timeframe, TradingMode } from '@/types/domain';

const enc = encodeURIComponent;
const toResult = (r: unknown, okMsg: string): CommandResult => {
  const o = (r && typeof r === 'object' ? r : {}) as Record<string, unknown>;
  return { ok: o.ok !== false, message: typeof o.message === 'string' ? o.message : okMsg, id: typeof o.id === 'string' ? o.id : undefined };
};

export const api = {
  status: async () => A.adaptStatus(await http.get('/api/status', 4000)),
  account: async () => A.adaptAccount(await http.get('/api/account')),
  candidates: async () => A.adaptCandidates(await http.get('/api/candidates')),
  positions: async () => A.adaptPositions(await http.get('/api/positions')),
  orders: async () => A.adaptOrders(await http.get('/api/orders')),
  trades: async () => A.adaptTrades(await http.get('/api/trades')),
  settings: async () => A.adaptSettings(await http.get('/api/settings')),
  saveSettings: async (body: { risk?: RiskSettings; strategy?: StrategySettings }) => toResult(await http.post('/api/settings', body), 'Настройки сохранены'),

  market: async (symbol: string, tf: Timeframe) => {
    const q = `?timeframe=${tf}`;
    const [m, oi, cvd] = await Promise.all([
      http.get(`/api/market/${enc(symbol)}${q}`),
      http.get(`/api/market/${enc(symbol)}/oi${q}`).catch(() => undefined),
      http.get(`/api/market/${enc(symbol)}/cvd${q}`).catch(() => undefined),
    ]);
    return A.adaptMarket(m, symbol, tf, oi, cvd);
  },
  geometry: async (symbol: string, tf: Timeframe, bars: number) =>
    A.adaptGeometry(await http.get(`/api/market/${enc(symbol)}/geometry?timeframe=${tf}&bars=${bars}`), symbol),

  openOrder: async (req: OpenOrderRequest) => toResult(await http.post('/api/order/open', req), 'Ордер отправлен'),
  closePosition: async (req: ClosePositionRequest) => toResult(await http.post('/api/order/close', req), 'Запрос на закрытие отправлен'),
  cancelOrders: async (body: { orderId?: string; symbol?: string; all?: boolean; mode: TradingMode }) => toResult(await http.post('/api/order/cancel', body), 'Ордера отменены'),
  setAutotrading: async (body: { enabled: boolean; mode: TradingMode; confirm?: string }) => toResult(await http.post('/api/autotrading', body), body.enabled ? 'Автоторговля включена' : 'Автоторговля выключена'),
  emergencyStop: async (reason: string) => toResult(await http.post('/api/emergency-stop', { reason, closePositions: true, cancelOrders: true }), 'Экстренная остановка выполнена'),
};
