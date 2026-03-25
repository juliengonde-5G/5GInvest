/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#0a0a0f",
          800: "#12121a",
          700: "#1a1a2e",
          600: "#252540",
          500: "#2d2d4a",
        },
        accent: {
          blue: "#6366f1",
          green: "#22c55e",
          red: "#ef4444",
          orange: "#f59e0b",
          purple: "#a855f7",
          cyan: "#06b6d4",
        },
      },
    },
  },
  plugins: [],
};
