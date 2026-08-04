"use client";

import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type TipoProcesso = Schemas["TipoProcessoResponse"];

function CadastroTipoProcessoForm({ onCriado }: { onCriado: () => void }) {
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.criarTipoProcesso({ nome });
      setNome("");
      onCriado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o tipo de processo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
      <div>
        <label htmlFor="nome-tipo" className="block text-sm">
          Nome do tipo de processo
        </label>
        <input
          id="nome-tipo"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          required
          className="mt-1 rounded border px-3 py-2 text-sm"
        />
      </div>

      {erro && <p className="mt-3 text-sm text-red-600">{erro}</p>}

      <button
        type="submit"
        disabled={enviando}
        className="mt-4 rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {enviando ? "Salvando…" : "Cadastrar tipo de processo"}
      </button>
    </form>
  );
}

// Linha de tipo de processo (change ajustes-ui-admin, design D4): estado de
// edição, salvamento e erro do prazo de anonimização são isolados por linha
// — salvar uma linha não altera nem revalida as demais. A única ação da
// linha é salvar o prazo; relayout puro, sem edição de nome, desativação ou
// exclusão, que não existem hoje.
function LinhaTipoProcesso({ tipo, onAtualizado }: { tipo: TipoProcesso; onAtualizado: () => void }) {
  const [valor, setValor] = useState(String(tipo.prazo_anonimizacao_anos));
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function salvar() {
    const anos = Number(valor);
    setErro(null);
    setSalvando(true);
    try {
      await api.atualizarTipoProcesso(tipo.id, { prazo_anonimizacao_anos: anos });
      onAtualizado();
    } catch (err) {
      setErro(
        err instanceof ApiError
          ? err.detail
          : "Não foi possível salvar o prazo de anonimização.",
      );
    } finally {
      setSalvando(false);
    }
  }

  return (
    <tr className="border-t align-top odd:bg-white even:bg-gray-50/50">
      <td className="px-3 py-2">{tipo.nome}</td>
      <td className="px-3 py-2">
        <label htmlFor={`prazo-${tipo.id}`} className="sr-only">
          Prazo de anonimização LGPD (anos) — {tipo.nome}
        </label>
        <input
          id={`prazo-${tipo.id}`}
          type="number"
          min={1}
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="w-24 rounded border px-2 py-1 text-sm"
        />
      </td>
      <td className="px-3 py-2">
        <div className="flex items-center gap-2 text-sm">
          <button type="button" onClick={() => void salvar()} disabled={salvando} className="text-navy-600">
            {salvando ? "Salvando…" : "Salvar"}
          </button>
          {erro && <span className="text-red-600">{erro}</span>}
        </div>
      </td>
    </tr>
  );
}

function AdminTiposProcessoConteudo() {
  const [tipos, setTipos] = useState<TipoProcesso[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  async function carregar() {
    try {
      setTipos(await api.listarTiposProcesso());
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os tipos de processo.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Tipos de processo</h1>

      <div className="mt-4">
        <CadastroTipoProcessoForm onCriado={carregar} />
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {!carregando && tipos.length === 0 && (
        <p className="mt-6 text-sm text-gray-500">Nenhum tipo de processo cadastrado.</p>
      )}

      {tipos.length > 0 && (
        <div className="mt-6 overflow-x-auto rounded-card border border-navy-50 bg-superficie-card shadow-card">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-xs font-medium uppercase tracking-wide text-gray-500">
                <th className="px-3 py-2">Nome</th>
                <th className="px-3 py-2">Prazo de anonimização LGPD (anos)</th>
                <th className="px-3 py-2">Ações</th>
              </tr>
            </thead>
            <tbody>
              {tipos.map((tipo) => (
                <LinhaTipoProcesso key={tipo.id} tipo={tipo} onAtualizado={carregar} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function AdminTiposProcessoPage() {
  // Cadastro/edição de tipo de processo é admin-only. O GET do catálogo é
  // aberto (Servidor precisa dele para criar processo, US 2.1), então sem
  // este guard a tela renderiza o formulário completo para qualquer sessão;
  // aqui bloqueamos no nível da página.
  return (
    <ProtectedShell perfisPermitidos={["administrador"]}>
      <AdminTiposProcessoConteudo />
    </ProtectedShell>
  );
}
