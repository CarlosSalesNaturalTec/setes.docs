"use client";

import { ProtectedShell } from "@/components/protected-shell";

import { SolicitacoesLgpdConteudo } from "./solicitacoes-lgpd-content";

export default function SolicitacoesLgpdPage() {
  return (
    <ProtectedShell perfisPermitidos={["administrador"]}>
      <SolicitacoesLgpdConteudo />
    </ProtectedShell>
  );
}
