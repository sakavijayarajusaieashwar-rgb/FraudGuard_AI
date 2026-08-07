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
          900: "var(--bg-primary)",
          800: "var(--slate-900)",
          700: "var(--slate-800)",
          600: "var(--slate-700)",
        },
        slate: {
          950: "var(--slate-950)",
          900: "var(--slate-900)",
          850: "var(--slate-850)",
          800: "var(--slate-800)",
          750: "var(--slate-750)",
          700: "var(--slate-700)",
          600: "var(--slate-600)",
          500: "var(--slate-500)",
          400: "var(--slate-400)",
          300: "var(--slate-300)",
          200: "var(--slate-200)",
          100: "var(--slate-100)",
          50: "var(--slate-50)",
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
