/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#09090b",
        card: "#0c0c0f",
        "card-hover": "#131316",
        border: "#1c1c22",
        "border-light": "#27272a",
        muted: "#a1a1aa",
        "muted-dark": "#71717a",
        sidebar: "#09090b",
        "sidebar-border": "#1c1c22",
        emerald: { 400: "#34d399", 500: "#10b981", 600: "#059669" },
        red: { 400: "#f87171", 500: "#ef4444" },
        amber: { 400: "#fbbf24", 500: "#f59e0b" },
        blue: { 400: "#60a5fa", 500: "#3b82f6" },
        violet: { 400: "#a78bfa", 500: "#8b5cf6" },
        cyan: { 400: "#22d3ee", 500: "#06b6d4" },
        rose: { 400: "#fb7185", 500: "#f43f5e" },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
