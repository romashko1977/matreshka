/**
 * Адаптеры ответов backend → доменные типы.
 * Backend на Python отдаёт snake_case — ключи приводятся к camelCase,
 * числа проверяются, отсутствующие поля получают безопасные значения.
 * Повреждённые записи отбрасываются, а не ломают интерфейс.
 */
import type {
  Account, Candidate, Candle, ChartOverlay, ConnectionInfo, GeometrySeries, LogEntry, MarketSnapshot, Order,
  PatternConfig, Position, RiskSettings, SeriesPoint, Side, StrategySettings, SystemStatus, Timeframe, Trade, TradingMode,
} from '@/types/domain';

type Obj = Record<string, unknown>;

const camel = (k: string) => k.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase());

export function camelize<T = unknown>(v: unknown): T {
  if (Array.isArray(v)) return v.map((x) => camelize(x)) as T;
  if (v && typeof v === 'object') {
    const out: Obj = {};
    for (const [k, val] of Object.entries(v as Obj)) out[camel(k)] = camelize(val);
    return out as T;
  }
  return v as T;
}

const isObj = (v: unknown): v is Obj => !!v && typeof v === 'object' && !Array.isArray(v);
const n = (v: unknown, d = 0) => {
  const x = typeof v === 'string' ? Number(v) : (v as number);
  return typeof x === 'number' && Number.isFinite(x) ? x : d;
};
const on = (v: unknown) => (v == null ? undefined : Number.isFinite(Number(v)) ? Number(v) : undefined);
const s = (v: unknown, d = '') => (typeof v === 'string' ? v : v == null ? d : String(v));
const b = (v: unknown, d = false) => (typeof v === 'boolean' ? v : d);
const ts = (v: unknown) => {
  if (typeof v === 'string') { const t = Date.parse(v); return Number.isFinite(t) ? t : 0; }
  const x = n(v);
  return x > 0 && x < 1e11 ? x * 1000 : x; // секунды → мс
};
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
/** Достаёт массив из {results:[...]}, {items:[...]}, {data:[...]} или просто [...]. */
export function list(v: unknown, ...keys: string[]): unknown[] {
  if (Array.isArray(v)) return v;
  if (isObj(v)) for (const k of [...keys, 'results', 'items', 'data']) if (Array.isArray(v[k])) return v[k] as unknown[];
  return [];
}

export function side(v: unknown): Side | undefined {
  const x = s(v).toLowerCase();
  if (x === 'long' || x === 'buy') return 'LONG';
  if (x === 'short' || x === 'sell') return 'SHORT';
  return undefined;
}

/** Режимы backend (monitor/paper/semi_auto/full_auto/live) → режимы интерфейса. */
export function mode(v: unknown): TradingMode {
  const x = s(v).toLowerCase();
  if (x === 'real' || x === 'live') return 'REAL';
  if (x === 'backtest') return 'BACKTEST';
  return 'PAPER';
}

export function adaptStatus(raw: unknown): SystemStatus {
  const o = camelize<Obj>(isObj(raw) ? raw : {});
  const tm = s(o.mode ?? o.tradingMode);
  return {
    engine: (['running', 'idle', 'stopped', 'emergency', 'error'].includes(s(o.engine)) ? s(o.engine) : s(o.status) === 'running' ? 'running' : 'unknown') as SystemStatus['engine'],
    engineMessage: s(o.engineMessage) || undefined,
    exchange: s(o.exchange, arr(o.connectedExchanges)[0] ? s(arr(o.connectedExchanges)[0]) : '—'),
    market: s(o.market, 'USDT-M Futures'),
    mode: mode(tm),
    // Автоторговлю считаем включённой только при явном true от backend.
    autotrading: o.autotrading === true || tm === 'full_auto',
    apiOk: true,
    version: s(o.version) || undefined,
    serverTime: ts(o.serverTime) || Date.now(),
    connectedExchanges: arr(o.connectedExchanges).map((x) => s(x)),
  };
}

export function adaptAccount(raw: unknown): Account {
  const o = camelize<Obj>(isObj(raw) ? raw : {});
  return {
    balance: n(o.balance), equity: n(o.equity, n(o.balance)), availableMargin: n(o.availableMargin),
    unrealizedPnl: n(o.unrealizedPnl), realizedPnl: n(o.realizedPnl), dayPnl: n(o.dayPnl),
    winRate: n(o.winRate), profitFactor: n(o.profitFactor), maxDrawdown: n(o.maxDrawdown),
    openPositions: n(o.openPositions), activeSignals: n(o.activeSignals), riskLevel: n(o.riskLevel),
    currency: s(o.currency, 'USDT'), ts: ts(o.ts) || Date.now(),
  };
}

export function adaptCandidate(raw: unknown, i: number): Candidate | null {
  if (!isObj(raw)) return null;
  const o = camelize<Obj>(raw);
  const fused = isObj(o.fused) ? o.fused : undefined; // формат /api/screener/scan
  const symbol = s(o.symbol);
  if (!symbol || o.error) return null;
  const score = n(o.score, fused ? Math.abs(n(fused.compositeScore)) : 0);
  const dir = side(o.direction ?? fused?.direction) ?? 'NEUTRAL';
  return {
    symbol, rank: n(o.rank, i + 1), price: n(o.price), change24h: n(o.change24h),
    volume24h: n(o.volume24h ?? o.volume), oi: n(o.oi), oiChange: n(o.oiChange), cvd: n(o.cvd),
    rsi: n(o.rsi, 50), volatility: n(o.volatility), direction: dir, score: Math.min(100, Math.max(0, score)),
    reason: s(o.reason, fused ? s(fused.aiComment) : ''), reasonCode: (s(o.reasonCode, 'custom') as Candidate['reasonCode']),
    leader: s(o.leader) || undefined, leaderLagSec: on(o.leaderLagSec),
    patterns: arr(o.patterns).filter(isObj).map((p) => ({ id: s(p.id, s(p.name)), name: s(p.name), state: (s(p.state, 'forming') as 'forming') })),
    signalAt: ts(o.signalAt ?? fused?.timestamp) || undefined,
    liquidity: (['high', 'mid', 'low'].includes(s(o.liquidity)) ? s(o.liquidity) : 'mid') as Candidate['liquidity'],
  };
}

export function adaptCandidates(raw: unknown): Candidate[] {
  return list(raw, 'candidates').map(adaptCandidate).filter((c): c is Candidate => !!c);
}

export function adaptCandles(raw: unknown): Candle[] {
  return list(raw, 'candles', 'ohlcv').map((r) => {
    if (Array.isArray(r)) return { time: Math.floor(ts(r[0]) / 1000), open: n(r[1]), high: n(r[2]), low: n(r[3]), close: n(r[4]), volume: n(r[5]) };
    const o = isObj(r) ? r : {};
    return { time: Math.floor(ts(o.time ?? o.timestamp ?? o.t) / 1000), open: n(o.open ?? o.o), high: n(o.high ?? o.h), low: n(o.low ?? o.l), close: n(o.close ?? o.c), volume: n(o.volume ?? o.v) };
  }).filter((c) => c.time > 0 && c.high >= c.low && c.close > 0).sort((a, b2) => a.time - b2.time);
}

export function adaptSeries(raw: unknown, key: string): SeriesPoint[] {
  return list(raw, key, 'series').map((r) => {
    if (Array.isArray(r)) return { time: Math.floor(ts(r[0]) / 1000), value: n(r[1]) };
    const o = isObj(r) ? camelize<Obj>(r) : {};
    return { time: Math.floor(ts(o.time ?? o.timestamp ?? o.t) / 1000), value: n(o.value ?? o[key] ?? o.v) };
  }).filter((p) => p.time > 0).sort((a, b2) => a.time - b2.time);
}

export function adaptOverlay(raw: unknown): ChartOverlay {
  const o = camelize<Obj>(isObj(raw) ? raw : {});
  return {
    levels: arr(o.levels).filter(isObj).map((l) => ({ price: n(l.price), kind: s(l.kind) === 'resistance' ? 'resistance' : 'support', strength: n(l.strength, 0.5) })),
    signals: arr(o.signals).filter(isObj).map((x) => ({ time: Math.floor(ts(x.time) / 1000), side: side(x.side) ?? 'LONG', label: s(x.label) })),
    patterns: arr(o.patterns).filter(isObj).map((x) => ({ time: Math.floor(ts(x.time) / 1000), name: s(x.name), side: side(x.side) ?? 'NEUTRAL' })),
    executions: arr(o.executions).filter(isObj).map((x) => ({ time: Math.floor(ts(x.time) / 1000), side: side(x.side) ?? 'LONG', kind: s(x.kind) === 'exit' ? 'exit' : 'entry', price: n(x.price) })),
  };
}

export function adaptMarket(raw: unknown, symbol: string, tf: Timeframe, oiRaw?: unknown, cvdRaw?: unknown): MarketSnapshot {
  const o = camelize<Obj>(isObj(raw) ? raw : {});
  const candles = adaptCandles(o.candles ?? raw);
  const last = candles[candles.length - 1]?.close ?? 0;
  return {
    symbol, timeframe: tf, candles,
    oi: adaptSeries(oiRaw ?? o.oi, 'oi'), cvd: adaptSeries(cvdRaw ?? o.cvd, 'cvd'),
    overlay: adaptOverlay(o.overlay),
    bid: n(o.bid, last), ask: n(o.ask, last),
  };
}

export function adaptPosition(raw: unknown): Position | null {
  if (!isObj(raw)) return null;
  const o = camelize<Obj>(raw);
  const sd = side(o.side); const sym = s(o.symbol);
  if (!sd || !sym) return null;
  return {
    id: s(o.id, sym + sd), symbol: sym, side: sd, size: n(o.size), entryPrice: n(o.entryPrice), markPrice: n(o.markPrice),
    leverage: n(o.leverage, 1), margin: n(o.margin), pnl: n(o.pnl ?? o.unrealizedPnl), pnlPct: n(o.pnlPct),
    stopLoss: on(o.stopLoss), takeProfit: on(o.takeProfit), liquidationPrice: on(o.liquidationPrice),
    openedAt: ts(o.openedAt) || Date.now(), source: s(o.source, 'backend'),
  };
}

export function adaptOrder(raw: unknown): Order | null {
  if (!isObj(raw)) return null;
  const o = camelize<Obj>(raw);
  const sd = side(o.side);
  if (!sd) return null;
  return { id: s(o.id), symbol: s(o.symbol), side: sd, type: s(o.type).toUpperCase() === 'LIMIT' ? 'LIMIT' : 'MARKET', price: on(o.price), size: n(o.size), status: (s(o.status, 'new') as Order['status']), reduceOnly: b(o.reduceOnly), createdAt: ts(o.createdAt) || Date.now() };
}

export function adaptTrade(raw: unknown): Trade | null {
  if (!isObj(raw)) return null;
  const o = camelize<Obj>(raw);
  const sd = side(o.side);
  if (!sd) return null;
  return {
    id: s(o.id), symbol: s(o.symbol), side: sd, entryPrice: n(o.entryPrice), exitPrice: n(o.exitPrice), size: n(o.size),
    pnl: n(o.pnl), pnlPct: n(o.pnlPct), openedAt: ts(o.openedAt), closedAt: ts(o.closedAt), source: s(o.source),
    exitReason: (s(o.exitReason, 'manual') as Trade['exitReason']), mode: mode(o.mode),
  };
}

export const adaptPositions = (r: unknown) => list(r, 'positions').map(adaptPosition).filter((x): x is Position => !!x);
export const adaptOrders = (r: unknown) => list(r, 'orders').map(adaptOrder).filter((x): x is Order => !!x);
export const adaptTrades = (r: unknown) => list(r, 'trades').map(adaptTrade).filter((x): x is Trade => !!x);

export function adaptSettings(raw: unknown): { risk?: Partial<RiskSettings>; strategy?: Partial<StrategySettings> } {
  const o = camelize<Obj>(isObj(raw) ? raw : {});
  const risk = isObj(o.risk) ? (o.risk as Partial<RiskSettings>) : undefined;
  const st = isObj(o.strategy) ? (o.strategy as Obj) : undefined;
  return {
    risk,
    strategy: st ? { ...st, patterns: arr(st.patterns).filter(isObj) as unknown as PatternConfig[] } as Partial<StrategySettings> : undefined,
  };
}

export function adaptGeometry(raw: unknown, symbol: string): GeometrySeries {
  const o = camelize<Obj>(isObj(raw) ? raw : {});
  const t = arr(o.t ?? o.time).map(ts);
  const len = t.length;
  const col = (k: string, d = 0) => { const a = arr(o[k]).map((x) => n(x, d)); return a.length === len ? a : new Array(len).fill(d); };
  return {
    symbol, t, price: col('price'), oi: col('oi'), cvd: col('cvd'), volume: col('volume'), completeness: col('completeness', 1),
    leader: s(o.leader) || undefined, lagBars: on(o.lagBars), correlation: on(o.correlation),
  };
}

export function adaptLog(raw: unknown, id: number): LogEntry | null {
  if (!isObj(raw)) return null;
  const o = camelize<Obj>(raw);
  return { id, ts: ts(o.ts ?? o.timestamp) || Date.now(), level: (s(o.level, 'info') as LogEntry['level']), category: (s(o.category, 'system') as LogEntry['category']), message: s(o.message), symbol: s(o.symbol) || undefined };
}

export function adaptConnections(raw: unknown): ConnectionInfo[] {
  return list(raw, 'connections').filter(isObj).map((c) => {
    const o = camelize<Obj>(c);
    return { id: s(o.id, s(o.name)), name: s(o.name), kind: (s(o.kind, 'exchange') as ConnectionInfo['kind']), state: (s(o.state, 'disconnected') as ConnectionInfo['state']), latencyMs: on(o.latencyMs), detail: s(o.detail), hasKey: b(o.hasKey) };
  });
}
