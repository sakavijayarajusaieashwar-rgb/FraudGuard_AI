/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#090d16",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155",
        },
        guard: {
          cyan: "#00f2fe",
          blue: "#4facfe",
          purple: "#7f53ac",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#ef4444"
        }
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s infinite',
        'trace-slide': 'traceSlide 0.3s ease-out forwards',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 15px rgba(0, 242, 254, 0.4)' },
          '50%': { opacity: 0.6, boxShadow: '0 0 5px rgba(0, 242, 254, 0.1)' },
        },
        traceSlide: {
          '0%': { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' }
        }
      }
    },
  },
  plugins: [],
}
