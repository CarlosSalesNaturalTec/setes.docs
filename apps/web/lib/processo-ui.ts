// Rótulos e utilitários de UI de processo/workflow (Épico 2). Mantém as
// colunas do Kanban alinhadas à máquina de estados do backend (aberto →
// em_tramitacao → concluido → arquivado) e os motivos de devolução ao enum.

import type { Schemas } from "@/lib/api";

export type StatusProcesso = "aberto" | "em_tramitacao" | "concluido" | "arquivado";

// Change visibilidade-processos-origem (design D4) — preferência do checkbox
// "Exibir concluídos e arquivados", desmarcado por padrão, persistida por
// navegador (não por usuário), mesmo padrão da chave do modo Kanban/Lista.
export const CHAVE_EXIBIR_FINALIZADOS = "setes:processos:exibir-finalizados";

// Mapeamento status→cor centralizado (D3): alimenta tanto o cabeçalho de
// coluna do Kanban quanto a pill de status da Lista, a partir dos tokens
// semânticos de `tailwind.config.ts` (`status.*`).
export const COLUNAS_KANBAN: { status: StatusProcesso; titulo: string; corClasse: string }[] = [
  { status: "aberto", titulo: "Aberto", corClasse: "bg-status-aberto-bg text-status-aberto" },
  {
    status: "em_tramitacao",
    titulo: "Em Tramitação",
    corClasse: "bg-status-tramitacao-bg text-status-tramitacao",
  },
  {
    status: "concluido",
    titulo: "Concluído",
    corClasse: "bg-status-concluido-bg text-status-concluido",
  },
  {
    status: "arquivado",
    titulo: "Arquivado",
    corClasse: "bg-status-arquivado-bg text-status-arquivado",
  },
];

export function corStatus(status: string): string {
  return (
    COLUNAS_KANBAN.find((c) => c.status === status)?.corClasse ?? "bg-gray-100 text-gray-700"
  );
}

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

// "Criado em dd/mm/aaaa hh:mm" para o card (Kanban e Lista).
export function textoCriadoEm(card: Card): string {
  const d = new Date(card.criado_em);
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `Criado em ${dd}/${mm}/${d.getFullYear()} ${hh}:${min}`;
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
