/** @type {import('tailwindcss').Config} */
// U05: theme colors are CSS variables so Dark/Light actually invert (index.css
// defines the values). The five accent colors use the channel form
// `rgb(var(--X-rgb) / <alpha-value>)` so Tailwind alpha modifiers (bg-success/10,
// border-error/20, …) resolve at runtime in BOTH themes. Surfaces read plain
// vars. This replaces the old hardcoded hex map that was Dark-only.
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--color-bg)',
        panel: 'var(--color-panel)',
        panel2: 'var(--color-panel2)',
        border: 'var(--color-border)',
        primary: 'rgb(var(--primary-rgb) / <alpha-value>)',
        secondary: 'rgb(var(--secondary-rgb) / <alpha-value>)',
        success: 'rgb(var(--success-rgb) / <alpha-value>)',
        warning: 'rgb(var(--warning-rgb) / <alpha-value>)',
        error: 'rgb(var(--error-rgb) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'Microsoft YaHei', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
