"use client";

import { useEffect, useState } from "react";

import { IconButton } from "@/components/icon-button";
import { IconBuildings, IconEdit, IconPowerOff, IconPowerOn } from "@/components/icons";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Unidade = Schemas["UnidadeResponse"];
type Setor = Schemas["SetorResponse"];

function CadastroUnidadeForm({ onCriada }: { onCriada: () => void }) {
  const [nome, setNome] = useState("");
  const [sigla, setSigla] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.cadastrarUnidade({ nome, sigla });
      setNome("");
      setSigla("");
      onCriada();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar a unidade.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
      <div>
        <label htmlFor="nome" className="block text-sm">
          Nome
        </label>
        <input
          id="nome"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          required
          className="mt-1 rounded border px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="sigla" className="block text-sm">
          Sigla
        </label>
        <input
          id="sigla"
          value={sigla}
          onChange={(e) => setSigla(e.target.value)}
          required
          className="mt-1 rounded border px-3 py-2 text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={enviando}
        className="rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {enviando ? "Salvando…" : "Cadastrar unidade"}
      </button>
      {erro && <p className="w-full text-sm text-red-600">{erro}</p>}
    </form>
  );
}

function LinhaUnidade({
  unidade,
  selecionada,
  onSelecionar,
  onAlterada,
}: {
  unidade: Unidade;
  selecionada: boolean;
  onSelecionar: () => void;
  onAlterada: () => void;
}) {
  const [editando, setEditando] = useState(false);
  const [nome, setNome] = useState(unidade.nome);
  const [sigla, setSigla] = useState(unidade.sigla);
  const [erro, setErro] = useState<string | null>(null);

  async function salvar() {
    setErro(null);
    try {
      await api.editarUnidade(unidade.id, { nome, sigla });
      setEditando(false);
      onAlterada();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível salvar.");
    }
  }

  async function desativar() {
    setErro(null);
    try {
      // Desativar a unidade cascateia para os setores (D3) — a confirmação
      // exibe a contagem de setores afetados antes de aplicar.
      const setores = await api.listarSetores(unidade.id, true);
      const aviso =
        setores.length > 0
          ? `Desativar "${unidade.nome}" também desativará ${setores.length} setor(es) desta unidade. ` +
            "A reativação da unidade não reativa os setores — cada um precisa ser reativado individualmente. Confirmar?"
          : `Desativar "${unidade.nome}"?`;
      if (!window.confirm(aviso)) return;

      await api.desativarUnidade(unidade.id);
      onAlterada();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível desativar.");
    }
  }

  async function reativar() {
    setErro(null);
    try {
      await api.reativarUnidade(unidade.id);
      onAlterada();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível reativar.");
    }
  }

  if (editando) {
    return (
      <tr className="border-t bg-navy-50/30">
        <td className="px-3 py-2">
          <input value={nome} onChange={(e) => setNome(e.target.value)} className="rounded border px-2 py-1 text-sm" />
        </td>
        <td className="px-3 py-2">
          <input value={sigla} onChange={(e) => setSigla(e.target.value)} className="rounded border px-2 py-1 text-sm" />
        </td>
        <td className="px-3 py-2">{unidade.ativo ? "Ativa" : "Inativa"}</td>
        <td className="space-x-2 px-3 py-2">
          <button onClick={salvar} className="text-sm text-navy-600">
            Salvar
          </button>
          <button onClick={() => setEditando(false)} className="text-sm text-gray-500">
            Cancelar
          </button>
        </td>
      </tr>
    );
  }

  return (
    <tr
      className={`border-t align-top hover:bg-navy-50/50 ${selecionada ? "bg-navy-50" : "odd:bg-white even:bg-gray-50/50"}`}
    >
      <td className="px-3 py-2">{unidade.nome}</td>
      <td className="px-3 py-2">{unidade.sigla}</td>
      <td className="px-3 py-2">{unidade.ativo ? "Ativa" : "Inativa"}</td>
      <td className="px-3 py-2">
        <div className="flex items-center gap-1">
          <IconButton label="Setores" onClick={onSelecionar} className="text-navy-600">
            <IconBuildings />
          </IconButton>
          <IconButton label="Editar" onClick={() => setEditando(true)} className="text-navy-600">
            <IconEdit />
          </IconButton>
          {unidade.ativo ? (
            <IconButton label="Desativar" onClick={desativar} className="text-red-600">
              <IconPowerOff />
            </IconButton>
          ) : (
            <IconButton label="Reativar" onClick={reativar} className="text-green-600">
              <IconPowerOn />
            </IconButton>
          )}
        </div>
        {erro && <p className="mt-1 text-xs text-red-600">{erro}</p>}
      </td>
    </tr>
  );
}

function LinhaSetor({ setor, onAlterado }: { setor: Setor; onAlterado: () => void }) {
  const [editando, setEditando] = useState(false);
  const [nome, setNome] = useState(setor.nome);
  const [sigla, setSigla] = useState(setor.sigla);
  const [erro, setErro] = useState<string | null>(null);

  async function executar(acao: () => Promise<unknown>, falha: string) {
    setErro(null);
    try {
      await acao();
      setEditando(false);
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : falha);
    }
  }

  if (editando) {
    return (
      <tr className="border-t bg-navy-50/30">
        <td className="px-3 py-2">
          <input
            value={nome}
            aria-label="Nome do setor"
            onChange={(e) => setNome(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
        </td>
        <td className="px-3 py-2">
          <input
            value={sigla}
            aria-label="Sigla do setor"
            onChange={(e) => setSigla(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
        </td>
        <td className="px-3 py-2">{setor.ativo ? "Ativo" : "Inativo"}</td>
        <td className="space-x-2 px-3 py-2">
          <button
            onClick={() => executar(() => api.editarSetor(setor.id, { nome, sigla }), "Não foi possível salvar.")}
            className="text-sm text-navy-600"
          >
            Salvar
          </button>
          <button onClick={() => setEditando(false)} className="text-sm text-gray-500">
            Cancelar
          </button>
          {erro && <p className="mt-1 text-xs text-red-600">{erro}</p>}
        </td>
      </tr>
    );
  }

  return (
    <tr className="border-t align-top odd:bg-white even:bg-gray-50/50">
      <td className="px-3 py-2">{setor.nome}</td>
      <td className="px-3 py-2">{setor.sigla}</td>
      <td className="px-3 py-2">{setor.ativo ? "Ativo" : "Inativo"}</td>
      <td className="px-3 py-2">
        {/* Nenhuma ação de exclusão: setor só é desativado/reativado (D3). */}
        <div className="flex items-center gap-1">
          <IconButton label={`Editar setor ${setor.sigla}`} onClick={() => setEditando(true)} className="text-navy-600">
            <IconEdit />
          </IconButton>
          {setor.ativo ? (
            <IconButton
              label={`Desativar setor ${setor.sigla}`}
              onClick={() => executar(() => api.desativarSetor(setor.id), "Não foi possível desativar.")}
              className="text-red-600"
            >
              <IconPowerOff />
            </IconButton>
          ) : (
            <IconButton
              label={`Reativar setor ${setor.sigla}`}
              onClick={() => executar(() => api.reativarSetor(setor.id), "Não foi possível reativar.")}
              className="text-green-600"
            >
              <IconPowerOn />
            </IconButton>
          )}
        </div>
        {erro && <p className="mt-1 text-xs text-red-600">{erro}</p>}
      </td>
    </tr>
  );
}

function SetoresDaUnidade({ unidade }: { unidade: Unidade }) {
  const [setores, setSetores] = useState<Setor[]>([]);
  const [nome, setNome] = useState("");
  const [sigla, setSigla] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [enviando, setEnviando] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      setSetores(await api.listarSetores(unidade.id));
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os setores.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidade.id]);

  async function cadastrar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.cadastrarSetor(unidade.id, { nome, sigla });
      setNome("");
      setSigla("");
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o setor.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="mt-8">
      <h2 className="text-lg font-medium">
        Setores de {unidade.nome} ({unidade.sigla})
      </h2>

      <form onSubmit={cadastrar} className="mt-3 flex flex-wrap items-end gap-3 rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
        <div>
          <label htmlFor="setor-nome" className="block text-sm">
            Nome do setor
          </label>
          <input
            id="setor-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="setor-sigla" className="block text-sm">
            Sigla do setor
          </label>
          <input
            id="setor-sigla"
            value={sigla}
            onChange={(e) => setSigla(e.target.value)}
            required
            maxLength={20}
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={enviando}
          className="rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Salvando…" : "Cadastrar setor"}
        </button>
        {erro && <p className="w-full text-sm text-red-600">{erro}</p>}
      </form>

      {carregando && <p className="mt-3 text-sm text-gray-500">Carregando…</p>}
      {!carregando && setores.length === 0 && (
        <p className="mt-3 text-sm text-gray-500">Nenhum setor cadastrado nesta unidade.</p>
      )}

      {setores.length > 0 && (
        // Contêiner rolável: rolagem horizontal fica na caixa, não na página (D1, D2)
        <div className="mt-3 overflow-x-auto rounded-card border border-navy-50 bg-superficie-card shadow-card">
          <table className="w-full min-w-[480px] text-left text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-xs font-medium uppercase tracking-wide text-gray-500">
                <th className="px-3 py-2">Nome</th>
                <th className="px-3 py-2">Sigla</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Ações</th>
              </tr>
            </thead>
            <tbody>
              {setores.map((s) => (
                <LinhaSetor key={s.id} setor={s} onAlterado={carregar} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function AdminUnidadesConteudo() {
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [unidadeSelecionadaId, setUnidadeSelecionadaId] = useState<string | null>(null);

  async function carregar() {
    try {
      setUnidades(await api.listarUnidades());
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar as unidades.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  const unidadeSelecionada = unidades.find((u) => u.id === unidadeSelecionadaId) ?? null;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Unidades administrativas</h1>

      <div className="mt-4">
        <CadastroUnidadeForm onCriada={carregar} />
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {/* Contêiner rolável: rolagem horizontal fica na caixa, não na página (D1, D2) */}
      <div className="mt-6 overflow-x-auto rounded-card border border-navy-50 bg-superficie-card shadow-card">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead>
            <tr className="border-b bg-gray-50 text-xs font-medium uppercase tracking-wide text-gray-500">
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Sigla</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {unidades.map((u) => (
              <LinhaUnidade
                key={u.id}
                unidade={u}
                selecionada={u.id === unidadeSelecionadaId}
                onSelecionar={() => setUnidadeSelecionadaId((atual) => (atual === u.id ? null : u.id))}
                onAlterada={carregar}
              />
            ))}
          </tbody>
        </table>
      </div>

      {unidadeSelecionada && <SetoresDaUnidade unidade={unidadeSelecionada} />}
    </div>
  );
}

export default function AdminUnidadesPage() {
  return (
    <ProtectedShell>
      <AdminUnidadesConteudo />
    </ProtectedShell>
  );
}
