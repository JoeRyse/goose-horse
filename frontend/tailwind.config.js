/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkbg: '#0b0f19',
        panel: '#131b2e',
        panelBorder: '#1e293b',
        lockEmerald: '#10b981',
        bestAmber: '#f59e0b',
        cyanAccent: '#06b6d4'
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'Roboto', 'sans-serif'],
      },
      animation: {
        'pulse-glow-emerald': 'pulseGlowEmerald 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-glow-amber': 'pulseGlowAmber 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        pulseGlowEmerald: {
          '0%, 100%': { boxShadow: '0 0 15px rgba(16, 185, 129, 0.6)' },
          '50%': { boxShadow: '0 0 25px rgba(16, 185, 129, 0.9)' },
        },
        pulseGlowAmber: {
          '0%, 100%': { boxShadow: '0 0 15px rgba(245, 158, 11, 0.6)' },
          '50%': { boxShadow: '0 0 25px rgba(245, 158, 11, 0.9)' },
        },
      },
    },
  },
  plugins: [],
}
