/**
 * Переподключаемый WebSocket с экспоненциальной задержкой, heartbeat
 * и измерением задержки. Сообщения — JSON вида { type, data, ts? }.
 */
import type { ConnState } from '@/types/domain';

export interface WsMessage { type: string; data: unknown; ts?: number }

interface Opts {
  url: string;
  onMessage: (m: WsMessage) => void;
  onState: (s: ConnState, info?: string) => void;
  onLatency?: (ms: number) => void;
  heartbeatMs?: number;
}

export class ReconnectingSocket {
  private ws: WebSocket | null = null;
  private attempt = 0;
  private closed = false;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private hbTimer: ReturnType<typeof setInterval> | null = null;
  private lastPing = 0;

  constructor(private readonly o: Opts) {}

  open() {
    this.closed = false;
    this.connect();
  }

  private connect() {
    if (this.closed) return;
    this.o.onState(this.attempt === 0 ? 'connecting' : 'reconnecting', this.attempt ? `попытка ${this.attempt}` : undefined);
    let ws: WebSocket;
    try {
      ws = new WebSocket(this.o.url);
    } catch (e) {
      this.o.onState('error', (e as Error).message);
      this.scheduleRetry();
      return;
    }
    this.ws = ws;
    ws.onopen = () => {
      this.attempt = 0;
      this.o.onState('connected');
      this.startHeartbeat();
    };
    ws.onmessage = (ev) => {
      let m: WsMessage;
      try {
        m = JSON.parse(typeof ev.data === 'string' ? ev.data : '');
      } catch {
        return; // повреждённое сообщение игнорируем
      }
      if (!m || typeof m.type !== 'string') return;
      if (m.type === 'pong') {
        if (this.lastPing) this.o.onLatency?.(performance.now() - this.lastPing);
        return;
      }
      if (typeof m.ts === 'number' && this.o.onLatency) {
        const lag = Date.now() - (m.ts < 1e11 ? m.ts * 1000 : m.ts);
        if (lag >= 0 && lag < 60_000) this.o.onLatency(lag);
      }
      this.o.onMessage(m);
    };
    ws.onerror = () => this.o.onState('error', 'ошибка сокета');
    ws.onclose = () => {
      this.stopHeartbeat();
      this.ws = null;
      if (this.closed) { this.o.onState('disconnected'); return; }
      this.scheduleRetry();
    };
  }

  private scheduleRetry() {
    this.attempt += 1;
    const delay = Math.min(30_000, 500 * 2 ** Math.min(this.attempt, 6)) + Math.random() * 400;
    this.o.onState('reconnecting', `через ${Math.round(delay / 1000)} с`);
    this.retryTimer = setTimeout(() => this.connect(), delay);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.hbTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.lastPing = performance.now();
        this.ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }));
      }
    }, this.o.heartbeatMs ?? 10_000);
  }

  private stopHeartbeat() {
    if (this.hbTimer) clearInterval(this.hbTimer);
    this.hbTimer = null;
  }

  send(obj: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(obj));
  }

  close() {
    this.closed = true;
    if (this.retryTimer) clearTimeout(this.retryTimer);
    this.stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }
}
