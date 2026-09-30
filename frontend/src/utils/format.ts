const nf = (min: number, max: number) => new Intl.NumberFormat('ru-RU', { minimumFractionDigits: min, maximumFractionDigits: max });
const cache = new Map<string, Intl.NumberFormat>();
function fmt(min: number, max: number) {
  const k = `${min}:${max}`;
  let f = cache.get(k);
  if (!f) { f = nf(min, max); cache.set(k, f); }
  return f;
}

export function priceDigits(p: number): number {
  const a = Math.abs(p);
  if (a >= 1000) return 2;
  if (a >= 10) return 3;
  if (a >= 1) return 4;
  if (a >= 0.01) return 5;
  return 7;
}

export const fmtPrice = (p: number | undefined | null) =>
  p == null || !Number.isFinite(p) ? '—' : fmt(priceDigits(p), priceDigits(p)).format(p);

export const fmtNum = (v: number | undefined | null, d = 2) =>
  v == null || !Number.isFinite(v) ? '—' : fmt(d, d).format(v);

export const fmtUsd = (v: number | undefined | null, d = 2) =>
  v == null || !Number.isFinite(v) ? '—' : `${fmt(d, d).format(v)} $`;

export const fmtSigned = (v: number | undefined | null, d = 2, suffix = '') =>
  v == null || !Number.isFinite(v) ? '—' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${fmt(d, d).format(Math.abs(v))}${suffix}`;

export const fmtPct = (frac: number | undefined | null, d = 2, signed = true) =>
  frac == null || !Number.isFinite(frac)
    ? '—'
    : signed ? fmtSigned(frac * 100, d, ' %') : `${fmt(d, d).format(frac * 100)} %`;

export function fmtCompact(v: number | undefined | null): string {
  if (v == null || !Number.isFinite(v)) return '—';
  const a = Math.abs(v);
  const s = v < 0 ? '−' : '';
  if (a >= 1e9) return `${s}${fmt(2, 2).format(a / 1e9)} B`;
  if (a >= 1e6) return `${s}${fmt(2, 2).format(a / 1e6)} M`;
  if (a >= 1e3) return `${s}${fmt(1, 1).format(a / 1e3)} K`;
  return `${s}${fmt(0, 2).format(a)}`;
}

export function fmtTime(ts: number | undefined, withMs = false): string {
  if (!ts) return '—';
  const d = new Date(ts);
  const p = (n: number, l = 2) => String(n).padStart(l, '0');
  const base = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
  return withMs ? `${base}.${p(d.getMilliseconds(), 3)}` : base;
}

export function fmtDateTime(ts: number | undefined): string {
  if (!ts) return '—';
  const d = new Date(ts);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getDate())}.${p(d.getMonth() + 1)} ${fmtTime(ts)}`;
}

export function fmtDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return '—';
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h >= 24) return `${Math.floor(h / 24)} д ${h % 24} ч`;
  if (h > 0) return `${h} ч ${m} мин`;
  if (m > 0) return `${m} мин ${s % 60} с`;
  return `${s} с`;
}

export function fmtAgo(ts: number | undefined, now = Date.now()): string {
  if (!ts) return '—';
  return `${fmtDuration(now - ts)} назад`;
}

export const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));
export const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
