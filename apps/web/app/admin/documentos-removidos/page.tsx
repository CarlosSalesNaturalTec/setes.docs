"use client";

import { ProtectedShell } from "@/components/protected-shell";

import { DocumentosRemovidosConteudo } from "./documentos-removidos-content";

export default function DocumentosRemovidosPage() {
  return (
    <ProtectedShell>
      <DocumentosRemovidosConteudo />
    </ProtectedShell>
  );
}
