import { describe, expect, it } from "vitest";

import type { Schemas } from "@/lib/api";
import { rotaInicial } from "@/lib/rota-inicial";

type Usuario = Schemas["UsuarioResumo"];

function usuario(perfil: string, pode_auditar = false): Usuario {
  return {
    id: "id-1",
    nome: "Usuário Teste",
    email: "teste@example.com",
    perfil,
    pode_auditar,
    status: "ativo",
  };
}

describe("rotaInicial", () => {
  it("direciona Servidor para /processos", () => {
    expect(rotaInicial(usuario("servidor"))).toBe("/processos");
  });

  it("direciona Gestor para /dashboard", () => {
    expect(rotaInicial(usuario("gestor"))).toBe("/dashboard");
  });

  it("direciona Administrador para /admin/unidades", () => {
    expect(rotaInicial(usuario("administrador"))).toBe("/admin/unidades");
  });

  it("direciona perfil desconhecido para /processos (fallback)", () => {
    expect(rotaInicial(usuario("perfil-inexistente"))).toBe("/processos");
  });

  it.each(["servidor", "gestor", "administrador"])(
    "permissão de auditoria sobrepõe o perfil %s",
    (perfil) => {
      expect(rotaInicial(usuario(perfil, true))).toBe("/auditoria/relatorios");
    },
  );
});
