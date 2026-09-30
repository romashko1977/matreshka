/** Дизайн-токены «Валькирии»: все цвета берутся из CSS-переменных (src/styles/tokens.css),
 *  поэтому светлая и тёмная темы переключаются без пересборки. */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`;

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: v('bg'),
        surface: v('surface'),
        raised: v('raised'),
        line: v('line'),
        ink: v('ink'),
        muted: v('muted'),
        faint: v('faint'),
        primary: v('primary'),
        profit: v('profit'),
        loss: v('loss'),
        gold: v('gold'),
        violet: v('violet'),
        info: v('info'),
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'Roboto', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      borderRadius: { card: '16px', ctl: '10px' },
      boxShadow: {
        glass: '0 1px 0 rgb(255 255 255 / 0.5) inset, 0 8px 28px -12px rgb(var(--shadow) / 0.35), 0 2px 6px -2px rgb(var(--shadow) / 0.18)',
        lift: '0 18px 40px -18px rgb(var(--shadow) / 0.45)',
        glowPrimary: '0 0 0 1px rgb(var(--primary) / 0.35), 0 0 22px -4px rgb(var(--primary) / 0.55)',
        glowProfit: '0 0 0 1px rgb(var(--profit) / 0.35), 0 0 20px -6px rgb(var(--profit) / 0.6)',
        glowLoss: '0 0 0 1px rgb(var(--loss) / 0.4), 0 0 20px -6px rgb(var(--loss) / 0.6)',
        glowGold: '0 0 0 1px rgb(var(--gold) / 0.45), 0 0 24px -6px rgb(var(--gold) / 0.65)',
      },
      transitionDuration: { 180: '180ms', 250: '250ms', 350: '350ms' },
      keyframes: {
        softPulse: {
          '0%,100%': { boxShadow: '0 0 0 1px rgb(var(--gold) / 0.35), 0 0 10px -4px rgb(var(--gold) / 0.35)' },
          '50%': { boxShadow: '0 0 0 1px rgb(var(--gold) / 0.6), 0 0 22px -4px rgb(var(--gold) / 0.6)' },
        },
        signalFlash: {
          '0%': { backgroundColor: 'rgb(var(--gold) / 0.28)' },
          '100%': { backgroundColor: 'transparent' },
        },
        dash: { to: { strokeDashoffset: '-24' } },
      },
      animation: {
        softPulse: 'softPulse 2.8s ease-in-out infinite',
        signalFlash: 'signalFlash 1.4s ease-out 1',
        dash: 'dash 1.2s linear infinite',
      },
    },
  },
  plugins: [],
};
