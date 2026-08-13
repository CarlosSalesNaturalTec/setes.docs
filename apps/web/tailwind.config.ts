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
        // Fundo do <main> do Login, tom derivado da amostra de borda de
        // login-hero.jpg escurecido para contraste >=3:1 contra o card branco
        // (D7, change login-logo-destaque). Exclusivo do Login — não usar em
        // outras telas sem nova decisão de design.
        marca: {
          destaque: "#126ced",
        },
        // Tokens semânticos de status do processo (D3, change
        // ajustar-visualizacao-processos) — cabeçalho de coluna do Kanban e
        // pill de status na Lista compartilham a mesma paleta.
        status: {
          aberto: "#1d4ed8",
          "aberto-bg": "#dbeafe",
          tramitacao: "#92400e",
          "tramitacao-bg": "#fef3c7",
          concluido: "#166534",
          "concluido-bg": "#dcfce7",
          arquivado: "#374151",
          "arquivado-bg": "#f3f4f6",
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
