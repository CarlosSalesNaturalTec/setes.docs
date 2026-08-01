"use client";

import { useEffect, useMemo, useState } from "react";

import { EditorFormatado } from "@/components/editor-formatado";
import { IconButton } from "@/components/icon-button";
import { IconEdit, IconPowerOff, IconPowerOn } from "@/components/icons";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Modelo = Schemas["ModeloResponse"];
type TipoModelo = Modelo["tipo"];

const TIPOS: { valor: TipoModelo; label: string }[] = [
  { valor: "requerimento", label: "Requerimento" },
  { valor: "oficio", label: "Ofício" },
  { valor: "memorando", label: "Memorando" },
  { valor: "despacho", label: "Despacho" },
  { valor: "parecer", label: "Parecer" },
  { valor: "nota_tecnica", label: "Nota técnica" },
  { valor: "relatorio", label: "Relatório" },
  { valor: "ata", label: "Ata" },
  { valor: "contrato", label: "Contrato" },
  { valor: "outro", label: "Outro" },
];

function labelTipo(tipo: TipoModelo): string {
  return TIPOS.find((t) => t.valor === tipo)?.label ?? tipo;
}

const AVISO_DADOS_PESSOAIS =
  "Este modelo é um catálogo reutilizável — não inclua dados pessoais reais (nome, CPF, " +
  "endereço). Use marcações de lacuna, como [NOME DO SOLICITANTE], para o servidor preencher " +
  "na abertura do processo.";

function CadastroModeloForm({ onCriado }: { onCriado: () => void }) {
  const [nome, setNome] = useState("");
  const [categoria, setCategoria] = useState("");
  const [tipo, setTipo] = useState<TipoModelo>("requerimento");
  const [descricao, setDescricao] = useState("");
  const [conteudo, setConteudo] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [resetKey, setResetKey] = useState(0);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.criarModelo({ nome, categoria, tipo, descricao: descricao || null, conteudo });
      setNome("");
      setCategoria("");
      setDescricao("");
      setConteudo("");
      setResetKey((k) => k + 1);
      onCriado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o modelo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="space-y-3 rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card"
    >
      <p className="rounded border border-amber-300 bg-amber-50 p-2 text-sm text-amber-800">
        {AVISO_DADOS_PESSOAIS}
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="modelo-nome" className="block text-sm">
            Nome
          </label>
          <input
            id="modelo-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="modelo-categoria" className="block text-sm">
            Categoria
          </label>
          <input
            id="modelo-categoria"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="modelo-tipo" className="block text-sm">
            Tipo
          </label>
          <select
            id="modelo-tipo"
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoModelo)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          >
            {TIPOS.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="modelo-descricao" className="block text-sm">
            Descrição (opcional)
          </label>
          <input
            id="modelo-descricao"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
      </div>
      <div>
        <span className="block text-sm">Conteúdo</span>
        <div className="mt-1">
          <EditorFormatado
            key={resetKey}
            valorInicial=""
            onChange={setConteudo}
            ariaLabel="Conteúdo do modelo"
          />
        </div>
      </div>
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      <button
        type="submit"
        disabled={enviando}
        className="rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {enviando ? "Salvando…" : "Cadastrar modelo"}
      </button>
    </form>
  );
}

function CartaoModelo({ modelo, onAlterado }: { modelo: Modelo; onAlterado: () => void }) {
  const [editando, setEditando] = useState(false);
  const [nome, setNome] = useState(modelo.nome);
  const [categoria, setCategoria] = useState(modelo.categoria);
  const [tipo, setTipo] = useState<TipoModelo>(modelo.tipo);
  const [descricao, setDescricao] = useState(modelo.descricao ?? "");
  const [conteudo, setConteudo] = useState(modelo.conteudo);
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function salvar() {
    setErro(null);
    setSalvando(true);
    try {
      await api.editarModelo(modelo.id, { nome, categoria, tipo, descricao: descricao || null, conteudo });
      setEditando(false);
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível salvar o modelo.");
    } finally {
      setSalvando(false);
    }
  }

  async function alternarSituacao() {
    setErro(null);
    try {
      if (modelo.ativo) await api.desativarModelo(modelo.id);
      else await api.reativarModelo(modelo.id);
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível alterar a situação.");
    }
  }

  if (editando) {
    return (
      <li className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            aria-label="Nome do modelo"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            className="rounded border px-3 py-2 text-sm"
          />
          <input
            aria-label="Categoria do modelo"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            className="rounded border px-3 py-2 text-sm"
          />
          <select
            aria-label="Tipo do modelo"
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoModelo)}
            className="rounded border px-3 py-2 text-sm"
          >
            {TIPOS.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.label}
              </option>
            ))}
          </select>
          <input
            aria-label="Descrição do modelo"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            className="rounded border px-3 py-2 text-sm"
          />
        </div>
        <div className="mt-3">
          <EditorFormatado valorInicial={conteudo} onChange={setConteudo} ariaLabel="Conteúdo do modelo" />
        </div>
        {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
        <div className="mt-3 flex gap-2">
          <button onClick={() => void salvar()} disabled={salvando} className="text-sm text-navy-600">
            {salvando ? "Salvando…" : "Salvar"}
          </button>
          <button onClick={() => setEditando(false)} className="text-sm text-gray-500">
            Cancelar
          </button>
        </div>
      </li>
    );
  }

  return (
    <li className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-medium">{modelo.nome}</h2>
          <p className="text-sm text-gray-500">
            {modelo.categoria} · {labelTipo(modelo.tipo)} · {modelo.ativo ? "Ativo" : "Inativo"}
          </p>
          {modelo.descricao && <p className="mt-1 text-sm text-gray-600">{modelo.descricao}</p>}
        </div>
        <div className="flex items-center gap-1">
          <IconButton label={`Editar ${modelo.nome}`} onClick={() => setEditando(true)} className="text-navy-600">
            <IconEdit />
          </IconButton>
          {modelo.ativo ? (
            <IconButton label={`Desativar ${modelo.nome}`} onClick={alternarSituacao} className="text-red-600">
              <IconPowerOff />
            </IconButton>
          ) : (
            <IconButton label={`Reativar ${modelo.nome}`} onClick={alternarSituacao} className="text-green-600">
              <IconPowerOn />
            </IconButton>
          )}
        </div>
      </div>
      {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
    </li>
  );
}

function AdminModelosConteudo() {
  const [modelos, setModelos] = useState<Modelo[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [filtroTipo, setFiltroTipo] = useState<TipoModelo | "">("");
  const [filtroSituacao, setFiltroSituacao] = useState<"todos" | "ativos" | "inativos">("todos");

  async function carregar() {
    try {
      setModelos(await api.listarModelos());
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os modelos.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  const modelosFiltrados = useMemo(
    () =>
      modelos.filter((m) => {
        if (filtroTipo && m.tipo !== filtroTipo) return false;
        if (filtroSituacao === "ativos" && !m.ativo) return false;
        if (filtroSituacao === "inativos" && m.ativo) return false;
        return true;
      }),
    [modelos, filtroTipo, filtroSituacao],
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold">Modelos de documento</h1>

      <div className="mt-4">
        <CadastroModeloForm onCriado={carregar} />
      </div>

      <div className="mt-6 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="filtro-tipo" className="block text-sm">
            Filtrar por tipo
          </label>
          <select
            id="filtro-tipo"
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value as TipoModelo | "")}
            className="mt-1 rounded border px-3 py-2 text-sm"
          >
            <option value="">Todos os tipos</option>
            {TIPOS.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filtro-situacao" className="block text-sm">
            Situação
          </label>
          <select
            id="filtro-situacao"
            value={filtroSituacao}
            onChange={(e) => setFiltroSituacao(e.target.value as "todos" | "ativos" | "inativos")}
            className="mt-1 rounded border px-3 py-2 text-sm"
          >
            <option value="todos">Todos</option>
            <option value="ativos">Ativos</option>
            <option value="inativos">Inativos</option>
          </select>
        </div>
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}
      {!carregando && modelosFiltrados.length === 0 && (
        <p className="mt-4 text-sm text-gray-500">Nenhum modelo encontrado.</p>
      )}

      <ul className="mt-4 space-y-4">
        {modelosFiltrados.map((modelo) => (
          <CartaoModelo key={modelo.id} modelo={modelo} onAlterado={carregar} />
        ))}
      </ul>
    </div>
  );
}

export default function AdminModelosPage() {
  return (
    <ProtectedShell perfisPermitidos={["administrador"]}>
      <AdminModelosConteudo />
    </ProtectedShell>
  );
}
