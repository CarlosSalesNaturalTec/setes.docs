"use client";

import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Unidade = Schemas["UnidadeResponse"];
type Usuario = Schemas["UsuarioResponse"];

function CadastroUnidadeForm({ usuarios, onCriada }: { usuarios: Usuario[]; onCriada: () => void }) {
  const [nome, setNome] = useState("");
  const [sigla, setSigla] = useState("");
  const [gestorId, setGestorId] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const gestores = usuarios.filter((u) => u.perfil === "gestor" || u.perfil === "administrador");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.cadastrarUnidade({ nome, sigla, gestor_responsavel_id: gestorId || null });
      setNome("");
      setSigla("");
      setGestorId("");
      onCriada();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar a unidade.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded border p-4">
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
      <div>
        <label htmlFor="gestor" className="block text-sm">
          Gestor responsável
        </label>
        <select
          id="gestor"
          value={gestorId}
          onChange={(e) => setGestorId(e.target.value)}
          className="mt-1 rounded border px-3 py-2 text-sm"
        >
          <option value="">(nenhum)</option>
          {gestores.map((g) => (
            <option key={g.id} value={g.id}>
              {g.nome}
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        disabled={enviando}
        className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {enviando ? "Salvando…" : "Cadastrar unidade"}
      </button>
      {erro && <p className="w-full text-sm text-red-600">{erro}</p>}
    </form>
  );
}

function LinhaUnidade({ unidade, onAlterada }: { unidade: Unidade; onAlterada: () => void }) {
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
      await api.desativarUnidade(unidade.id);
      onAlterada();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível desativar.");
    }
  }

  if (editando) {
    return (
      <tr className="border-t">
        <td className="p-2">
          <input value={nome} onChange={(e) => setNome(e.target.value)} className="rounded border px-2 py-1 text-sm" />
        </td>
        <td className="p-2">
          <input value={sigla} onChange={(e) => setSigla(e.target.value)} className="rounded border px-2 py-1 text-sm" />
        </td>
        <td className="p-2">{unidade.ativo ? "Ativa" : "Inativa"}</td>
        <td className="p-2 space-x-2">
          <button onClick={salvar} className="text-sm text-blue-600">
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
    <tr className="border-t align-top">
      <td className="p-2">{unidade.nome}</td>
      <td className="p-2">{unidade.sigla}</td>
      <td className="p-2">{unidade.ativo ? "Ativa" : "Inativa"}</td>
      <td className="p-2 space-x-2">
        <button onClick={() => setEditando(true)} className="text-sm text-blue-600">
          Editar
        </button>
        {unidade.ativo && (
          <button onClick={desativar} className="text-sm text-red-600">
            Desativar
          </button>
        )}
        {erro && <p className="text-xs text-red-600">{erro}</p>}
      </td>
    </tr>
  );
}

function AdminUnidadesConteudo() {
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  async function carregar() {
    try {
      const [listaUnidades, listaUsuarios] = await Promise.all([api.listarUnidades(), api.listarUsuarios()]);
      setUnidades(listaUnidades);
      setUsuarios(listaUsuarios.items);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar as unidades.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Unidades administrativas</h1>

      <div className="mt-4">
        <CadastroUnidadeForm usuarios={usuarios} onCriada={carregar} />
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b font-medium">
            <th className="p-2">Nome</th>
            <th className="p-2">Sigla</th>
            <th className="p-2">Status</th>
            <th className="p-2">Ações</th>
          </tr>
        </thead>
        <tbody>
          {unidades.map((u) => (
            <LinhaUnidade key={u.id} unidade={u} onAlterada={carregar} />
          ))}
        </tbody>
      </table>
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
