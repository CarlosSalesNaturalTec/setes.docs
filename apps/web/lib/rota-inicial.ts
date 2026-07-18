import type { Schemas } from "@/lib/api";

const PERFIS_CONHECIDOS = ["servidor", "gestor", "administrador"] as const;
type PerfilConhecido = (typeof PERFIS_CONHECIDOS)[number];

function ehPerfilConhecido(perfil: string): perfil is PerfilConhecido {
  return (PERFIS_CONHECIDOS as readonly string[]).includes(perfil);
}

function rotaPorPerfil(perfil: PerfilConhecido): string {
  switch (perfil) {
    case "servidor":
      return "/processos";
    case "gestor":
      return "/dashboard";
    case "administrador":
      return "/admin/unidades";
  }
}

/** Resolve a tela de aterrissagem pós-login/raiz — auditoria sobrepõe o
 * perfil (US 1.3 Cen.1); perfil desconhecido cai no fallback defensivo. */
export function rotaInicial(usuario: Schemas["UsuarioResumo"]): string {
  if (usuario.pode_auditar) return "/auditoria/relatorios";
  return ehPerfilConhecido(usuario.perfil) ? rotaPorPerfil(usuario.perfil) : "/processos";
}
