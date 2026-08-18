/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0d1117',
        panel: '#161b22',
        panel2: '#111820',
        border: 'rgba(255,255,255,0.08)',
        primary: '#00d4ff',
        secondary: '#7c6cf0',
        success: '#00d084',
        warning: '#ffb020',
        error: '#ff4d4f',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'Microsoft YaHei', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}