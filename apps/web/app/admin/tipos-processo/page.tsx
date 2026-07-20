"use client";

import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Unidade = Schemas["UnidadeResponse"];
type TipoProcesso = Schemas["TipoProcessoResponse"];

function nomeUnidade(unidades: Unidade[], unidadeId: string): string {
  return unidades.find((u) => u.id === unidadeId)?.sigla ?? unidadeId;
}

function EditorRoteiro({
  unidades,
  etapas,
  onChange,
}: {
  unidades: Unidade[];
  etapas: string[];
  onChange: (etapas: string[]) => void;
}) {
  const [selecionada, setSelecionada] = useState("");
  const unidadesAtivas = unidades.filter((u) => u.ativo);

  function adicionar() {
    if (!selecionada) return;
    onChange([...etapas, selecionada]);
    setSelecionada("");
  }

  function remover(index: number) {
    onChange(etapas.filter((_, i) => i !== index));
  }

  function mover(index: number, direcao: -1 | 1) {
    const alvo = index + direcao;
    if (alvo < 0 || alvo >= etapas.length) return;
    const nova = [...etapas];
    [nova[index], nova[alvo]] = [nova[alvo], nova[index]];
    onChange(nova);
  }

  return (
    <div>
      <div className="flex items-end gap-2">
        <div>
          <label htmlFor="unidade-etapa" className="block text-sm">
            Adicionar unidade ao roteiro
          </label>
          <select
            id="unidade-etapa"
            value={selecionada}
            onChange={(e) => setSelecionada(e.target.value)}
            className="mt-1 rounded border px-3 py-2 text-sm"
          >
            <option value="">Selecione…</option>
            {unidadesAtivas.map((u) => (
              <option key={u.id} value={u.id}>
                {u.nome}
              </option>
            ))}
          </select>
        </div>
        <button type="button" onClick={adicionar} className="rounded border px-3 py-2 text-sm">
          Adicionar etapa
        </button>
      </div>

      <ol className="mt-3 space-y-1">
        {etapas.map((unidadeId, index) => (
          <li key={`${unidadeId}-${index}`} className="flex items-center gap-2 text-sm">
            <span className="w-6 text-gray-400">{index + 1}.</span>
            <span className="flex-1">{nomeUnidade(unidades, unidadeId)}</span>
            <button type="button" onClick={() => mover(index, -1)} className="text-gray-500">
              ↑
            </button>
            <button type="button" onClick={() => mover(index, 1)} className="text-gray-500">
              ↓
            </button>
            <button type="button" onClick={() => remover(index)} className="text-red-600">
              remover
            </button>
          </li>
        ))}
        {etapas.length === 0 && <p className="text-sm text-gray-500">Nenhuma etapa adicionada.</p>}
      </ol>
    </div>
  );
}

function CadastroTipoProcessoForm({ unidades, onCriado }: { unidades: Unidade[]; onCriado: () => void }) {
  const [nome, setNome] = useState("");
  const [etapas, setEtapas] = useState<string[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.criarTipoProcesso({ nome, unidade_ids: etapas });
      setNome("");
      setEtapas([]);
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

      <div className="mt-4">
        <EditorRoteiro unidades={unidades} etapas={etapas} onChange={setEtapas} />
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

function EditorRoteiroExistente({
  tipo,
  unidades,
  onAtualizado,
}: {
  tipo: TipoProcesso;
  unidades: Unidade[];
  onAtualizado: () => void;
}) {
  const [editando, setEditando] = useState(false);
  const [etapas, setEtapas] = useState<string[]>(tipo.roteiro.etapas.map((e) => e.unidade_id));
  const [erro, setErro] = useState<string | null>(null);

  async function salvar() {
    setErro(null);
    try {
      await api.atualizarRoteiro(tipo.id, { unidade_ids: etapas });
      setEditando(false);
      onAtualizado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível salvar o roteiro.");
    }
  }

  if (!editando) {
    return (
      <div className="mt-2 text-sm">
        <p className="text-gray-700">
          {tipo.roteiro.etapas.map((e) => nomeUnidade(unidades, e.unidade_id)).join(" → ")}
        </p>
        <button onClick={() => setEditando(true)} className="mt-1 text-navy-600">
          Editar roteiro
        </button>
      </div>
    );
  }

  return (
    <div className="mt-2">
      <EditorRoteiro unidades={unidades} etapas={etapas} onChange={setEtapas} />
      {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
      <div className="mt-2 space-x-2">
        <button onClick={salvar} className="text-sm text-navy-600">
          Salvar nova versão
        </button>
        <button onClick={() => setEditando(false)} className="text-sm text-gray-500">
          Cancelar
        </button>
      </div>
    </div>
  );
}

function PrazoAnonimizacaoLgpd({ tipo, onAtualizado }: { tipo: TipoProcesso; onAtualizado: () => void }) {
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
    <div className="mt-3 flex items-end gap-2 text-sm">
      <div>
        <label htmlFor={`prazo-${tipo.id}`} className="block text-gray-600">
          Prazo de anonimização LGPD (anos)
        </label>
        <input
          id={`prazo-${tipo.id}`}
          type="number"
          min={1}
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          className="mt-1 w-24 rounded border px-2 py-1"
        />
      </div>
      <button type="button" onClick={() => void salvar()} disabled={salvando} className="text-navy-600">
        {salvando ? "Salvando…" : "Salvar"}
      </button>
      {erro && <span className="text-red-600">{erro}</span>}
    </div>
  );
}

function AdminTiposProcessoConteudo() {
  const [tipos, setTipos] = useState<TipoProcesso[]>([]);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  async function carregar() {
    try {
      const [listaTipos, listaUnidades] = await Promise.all([
        api.listarTiposProcesso(),
        api.listarUnidades(),
      ]);
      setTipos(listaTipos);
      setUnidades(listaUnidades);
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
      <h1 className="text-2xl font-semibold">Tipos de processo e roteiros</h1>

      <div className="mt-4">
        <CadastroTipoProcessoForm unidades={unidades} onCriado={carregar} />
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      <ul className="mt-6 space-y-4">
        {tipos.map((tipo) => (
          <li key={tipo.id} className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
            <h2 className="font-medium">{tipo.nome}</h2>
            <EditorRoteiroExistente tipo={tipo} unidades={unidades} onAtualizado={carregar} />
            <PrazoAnonimizacaoLgpd tipo={tipo} onAtualizado={carregar} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AdminTiposProcessoPage() {
  // US 8.2 — cadastro/edição de tipos de processo e roteiros é admin-only.
  // O GET do catálogo é aberto (Servidor precisa dele para criar processo,
  // US 2.1), então sem este guard a tela renderiza o formulário completo para
  // qualquer sessão; aqui bloqueamos no nível da página.
  return (
    <ProtectedShell perfisPermitidos={["administrador"]}>
      <AdminTiposProcessoConteudo />
    </ProtectedShell>
  );
}
