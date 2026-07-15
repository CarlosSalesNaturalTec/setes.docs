// Rótulos e utilitários de UI de processo/workflow (Épico 2). Mantém as
// colunas do Kanban alinhadas à máquina de estados do backend (aberto →
// em_tramitacao → concluido → arquivado) e os motivos de devolução ao enum.

import type { Schemas } from "@/lib/api";

export type StatusProcesso = "aberto" | "em_tramitacao" | "concluido" | "arquivado";

export const COLUNAS_KANBAN: { status: StatusProcesso; titulo: string }[] = [
  { status: "aberto", titulo: "Aberto" },
  { status: "em_tramitacao", titulo: "Em Tramitação" },
  { status: "concluido", titulo: "Concluído" },
  { status: "arquivado", titulo: "Arquivado" },
];

export const MOTIVOS_DEVOLUCAO: { valor: string; rotulo: string }[] = [
  { valor: "documentacao_insuficiente", rotulo: "Documentação insuficiente" },
  { valor: "correcao_dados", rotulo: "Correção de dados" },
  { valor: "diligencia_complementar", rotulo: "Diligência complementar" },
];

const ROTULO_EVENTO: Record<string, string> = {
  despacho: "Despacho",
  devolucao: "Devolução",
  conclusao: "Conclusão",
};

export function rotuloEvento(tipo: string): string {
  return ROTULO_EVENTO[tipo] ?? tipo;
}

export function rotuloStatus(status: string): string {
  return COLUNAS_KANBAN.find((c) => c.status === status)?.titulo ?? status;
}

type Card = Schemas["CardProcessoResponse"];

export function agruparPorStatus(itens: Card[]): Record<StatusProcesso, Card[]> {
  const grupos: Record<StatusProcesso, Card[]> = {
    aberto: [],
    em_tramitacao: [],
    concluido: [],
    arquivado: [],
  };
  for (const item of itens) {
    const status = item.status as StatusProcesso;
    if (grupos[status]) grupos[status].push(item);
  }
  return grupos;
}

// Texto de "dias restantes"/"vencido" para o card (US 2.3 Cen.4).
export function textoPrazo(card: Card): string {
  if (card.vencido) {
    const dias = Math.abs(card.dias_restantes);
    return `Vencido há ${dias} dia${dias === 1 ? "" : "s"}`;
  }
  if (card.dias_restantes === 0) return "Vence hoje";
  return `${card.dias_restantes} dia${card.dias_restantes === 1 ? "" : "s"} restante${card.dias_restantes === 1 ? "" : "s"}`;
}
