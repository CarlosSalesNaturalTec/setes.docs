import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { NOME_PRODUTO } from "@/lib/marca";

// `icons` não é declarado (D5, change marca-visual-despapelize): `app/icon.svg`
// já é servido pela convenção de arquivo do App Router, que injeta o próprio
// `<link rel="icon">` com cache-busting. Verificado: /icon.svg respondia 200
// mesmo sem esta declaração — ela era redundante.
export const metadata: Metadata = {
  title: NOME_PRODUTO,
  description: "Gestor de processos e tramitação",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
