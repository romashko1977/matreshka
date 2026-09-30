/**
 * Доменные типы «Валькирии». Это контракт между интерфейсом и backend:
 * адаптеры в src/api/adapters.ts приводят ответы FastAPI к этим формам.
 * Все цены — number в валюте котировки (USDT), время — unix ms.
 */

export type TradingMode = 'REAL' | 'PAPER' | 'BACKTEST';
export type Side = 'LONG' | 'SHORT';
export type OrderType = 'MARKET' | 'LIMIT';
export type Timeframe = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
export const TIMEFRAMES: Timeframe[] = ['1m', '5m', '15m', '1h', '4h', '1d'];

export type ConnState = 'connected' | 'connecting' | 'reconnecting' | 'disconnected' | 'error';
export type EngineState = 'running' | 'idle' | 'stopped' | 'emergency' | 'error' | 'unknown';

export interface SystemStatus {
  engine: EngineState;
  engineMessage?: string;
  exchange: string;
  market: string;               // например «USDT-M Futures»
  mode: TradingMode;
  autotrading: boolean;
  apiOk: boolean;
  version?: string;
  serverTime: number;
  connectedExchanges: string[];
}

export interface Account {
  balance: number;
  equity: number;
  availableMargin: number;
  unrealizedPnl: number;
  realizedPnl: number;
  dayPnl: number;
  winRate: number;              // 0..1
  profitFactor: number;
  maxDrawdown: number;          // 0..1
  openPositions: number;
  activeSignals: number;
  riskLevel: number;            // 0..1 — доля использованного риск-бюджета
  currency: string;
  ts: number;
}

export interface Candidate {
  symbol: string;
  rank: number;
  price: number;
  change24h: number;            // доля: 0.034 = +3.4 %
  volume24h: number;            // в USDT
  oi: number;                   // в USDT
  oiChange: number;             // доля за окно
  cvd: number;                  // в USDT, накопленная дельта за окно
  rsi: number;
  volatility: number;           // доля (ATR/цена)
  direction: Side | 'NEUTRAL';
  score: number;                // 0..100
  reason: string;
  reasonCode: ReasonCode;
  leader?: string;
  leaderLagSec?: number;
  patterns: PatternHit[];
  signalAt?: number;
  liquidity: 'high' | 'mid' | 'low';
}

export type ReasonCode = 'impulse' | 'trap' | 'gartley' | 'divergence' | 'volume' | 'exhaustion' | 'leader' | 'correlation' | 'custom';

export interface PatternHit {
  id: string;
  name: string;
  state: 'confirmed' | 'forming' | 'rejected';
}

export interface Candle {
  time: number;                 // unix seconds (формат lightweight-charts)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SeriesPoint { time: number; value: number }

export interface ChartOverlay {
  levels: { price: number; kind: 'support' | 'resistance'; strength: number }[];
  signals: { time: number; side: Side; label: string }[];
  patterns: { time: number; name: string; side: Side | 'NEUTRAL' }[];
  executions: { time: number; side: Side; kind: 'entry' | 'exit'; price: number }[];
}

export interface MarketSnapshot {
  symbol: string;
  timeframe: Timeframe;
  candles: Candle[];
  oi: SeriesPoint[];
  cvd: SeriesPoint[];
  overlay: ChartOverlay;
  bid: number;
  ask: number;
}

export interface Position {
  id: string;
  symbol: string;
  side: Side;
  size: number;                 // в монетах
  entryPrice: number;
  markPrice: number;
  leverage: number;
  margin: number;
  pnl: number;
  pnlPct: number;               // к марже
  stopLoss?: number;
  takeProfit?: number;
  liquidationPrice?: number;
  openedAt: number;
  source: string;               // стратегия/паттерн или «ручной»
}

export interface Order {
  id: string;
  symbol: string;
  side: Side;
  type: OrderType;
  price?: number;
  size: number;
  status: 'new' | 'partially_filled' | 'filled' | 'cancelled' | 'rejected';
  reduceOnly?: boolean;
  createdAt: number;
}

export interface Trade {
  id: string;
  symbol: string;
  side: Side;
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  pnlPct: number;
  openedAt: number;
  closedAt: number;
  source: string;
  exitReason: 'tp' | 'sl' | 'manual' | 'signal' | 'emergency';
  mode: TradingMode;
}

export type CombineMode = 'ANY' | 'ALL' | 'WEIGHTED' | 'CUSTOM';

export interface PatternConfig {
  id: string;
  name: string;
  group: string;
  description: string;
  enabled: boolean;
  standalone: boolean;          // может давать сигнал самостоятельно
  confirm: boolean;             // участвует в совместном подтверждении
  weight: number;               // 0..1
  minScore: number;             // 0..100
  timeframe: Timeframe;
  status: 'active' | 'paused' | 'error' | 'warming';
  lastFiredAt?: number;
  signals: number;
  winRate: number;
  avgResult: number;            // доля на сделку
  lastSkipReason?: string;
}

export interface StrategySettings {
  combineMode: CombineMode;
  weightedThreshold: number;    // 0..1 для WEIGHTED
  customExpression: string;     // для CUSTOM
  patterns: PatternConfig[];
}

export interface RiskSettings {
  maxRiskPerTradePct: number;
  maxDailyLossPct: number;
  maxDrawdownPct: number;
  maxPositions: number;
  maxPositionUsd: number;
  maxLeverage: number;
  maxPerSymbol: number;
  maxCorrelated: number;
  correlationThreshold: number;
  cooldownAfterLossMin: number;
  killSwitch: boolean;
  stopOnDisconnect: boolean;
  stopOnStaleData: boolean;
  staleDataSec: number;
  requireStopLoss: boolean;
}

export interface OpenOrderRequest {
  symbol: string;
  side: Side;
  type: OrderType;
  price?: number;
  sizeUsd: number;
  leverage: number;
  stopLoss?: number;
  takeProfit?: number;
  mode: TradingMode;
  clientId: string;
}

export interface ClosePositionRequest { positionId: string; fraction: number; mode: TradingMode }

export interface CommandResult { ok: boolean; message: string; id?: string }

export type LogLevel = 'debug' | 'info' | 'signal' | 'order' | 'warn' | 'risk' | 'error';
export type LogCategory = 'signal' | 'order' | 'api' | 'ws' | 'skip' | 'block' | 'settings' | 'user' | 'risk' | 'system';

export interface LogEntry {
  id: number;
  ts: number;                   // unix ms
  level: LogLevel;
  category: LogCategory;
  message: string;
  symbol?: string;
}

/** 3D-геометрия: сырые нормализованные ряды, из которых воркер строит спирали. */
export interface GeometrySeries {
  symbol: string;
  t: number[];                  // unix ms
  price: number[];
  oi: number[];
  cvd: number[];
  volume: number[];
  completeness: number[];       // 0..1 — полнота/достоверность точки
  leader?: string;
  lagBars?: number;
  correlation?: number;         // корреляция с поводырём
}

export interface BacktestResult {
  id: string;
  strategy: string;
  from: number;
  to: number;
  trades: number;
  winRate: number;
  profitFactor: number;
  pnlPct: number;
  maxDrawdown: number;
  sharpe: number;
  equity: SeriesPoint[];
}

export interface ConnectionInfo {
  id: string;
  name: string;
  kind: 'exchange' | 'data' | 'notify' | 'ai';
  state: ConnState;
  latencyMs?: number;
  detail: string;
  hasKey: boolean;              // ключ настроен на backend (само значение никогда не передаётся)
}
