import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#eef2f8",
          600: "#2f5a8a",
          700: "#274b74",
          900: "#1e3a5f",
        },
        superficie: {
          app: "#f5f7fa",
          card: "#ffffff",
        },
      },
      borderRadius: {
        card: "0.75rem",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(30 58 95 / 0.1), 0 1px 2px -1px rgb(30 58 95 / 0.1)",
      },
    },
  },
  plugins: [],
} satisfies Config;
