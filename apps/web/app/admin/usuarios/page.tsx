"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Unidade = Schemas["UnidadeResponse"];
type Usuario = Schemas["UsuarioResponse"];
type Perfil = Schemas["CadastroUsuarioRequest"]["perfil"];

function nomeUnidade(unidades: Unidade[], unidadeId: string | null): string {
  if (!unidadeId) return "—";
  return unidades.find((u) => u.id === unidadeId)?.nome ?? unidadeId;
}

function CadastroUsuarioForm({
  unidades,
  perfilAtual,
  onCriado,
}: {
  unidades: Unidade[];
  perfilAtual: Perfil;
  onCriado: () => void;
}) {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [perfil, setPerfil] = useState<Perfil>("servidor");
  const [unidadeId, setUnidadeId] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Gestor só pode cadastrar Servidor (US 1.2 Cen.3) — nem oferece a opção.
  const perfisPermitidos: Perfil[] = perfilAtual === "administrador" ? ["servidor", "gestor", "administrador"] : ["servidor"];

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setMensagem(null);
    setEnviando(true);
    try {
      await api.cadastrarUsuario({ nome, email, perfil, unidade_id: unidadeId || null });
      setMensagem(`Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${email}.`);
      setNome("");
      setEmail("");
      setPerfil("servidor");
      setUnidadeId("");
      onCriado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o usuário.");
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
        <label htmlFor="email" className="block text-sm">
          E-mail
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mt-1 rounded border px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="perfil" className="block text-sm">
          Perfil
        </label>
        <select
          id="perfil"
          value={perfil}
          onChange={(e) => setPerfil(e.target.value as Perfil)}
          className="mt-1 rounded border px-3 py-2 text-sm"
        >
          {perfisPermitidos.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="unidade" className="block text-sm">
          Unidade
        </label>
        <select
          id="unidade"
          value={unidadeId}
          onChange={(e) => setUnidadeId(e.target.value)}
          className="mt-1 rounded border px-3 py-2 text-sm"
        >
          <option value="">(nenhuma)</option>
          {unidades.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nome}
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        disabled={enviando}
        className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {enviando ? "Salvando…" : "Cadastrar usuário"}
      </button>
      {erro && <p className="w-full text-sm text-red-600">{erro}</p>}
      {mensagem && <p className="w-full text-sm text-green-700">{mensagem}</p>}
    </form>
  );
}

function AcaoTransferirUnidade({
  usuario,
  unidades,
  onAlterado,
}: {
  usuario: Usuario;
  unidades: Unidade[];
  onAlterado: () => void;
}) {
  const [aberto, setAberto] = useState(false);
  const [unidadeId, setUnidadeId] = useState(usuario.unidade_id ?? "");
  const [erro, setErro] = useState<string | null>(null);

  async function confirmar() {
    setErro(null);
    try {
      await api.transferirUnidade(usuario.id, { unidade_id: unidadeId });
      setAberto(false);
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível transferir.");
    }
  }

  if (!aberto) {
    return (
      <button onClick={() => setAberto(true)} className="text-sm text-blue-600">
        Transferir unidade
      </button>
    );
  }

  return (
    <div className="text-sm">
      <select value={unidadeId} onChange={(e) => setUnidadeId(e.target.value)} className="rounded border px-2 py-1">
        <option value="">Selecione…</option>
        {unidades.map((u) => (
          <option key={u.id} value={u.id}>
            {u.nome}
          </option>
        ))}
      </select>
      <button onClick={confirmar} className="ml-2 text-blue-600">
        Confirmar
      </button>
      <button onClick={() => setAberto(false)} className="ml-2 text-gray-500">
        Cancelar
      </button>
      {erro && <p className="text-red-600">{erro}</p>}
    </div>
  );
}

function AcaoUnidadesGeridas({ usuario, unidades }: { usuario: Usuario; unidades: Unidade[] }) {
  const [aberto, setAberto] = useState(false);
  const [selecionadas, setSelecionadas] = useState<string[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function abrir() {
    setAberto(true);
    setCarregando(true);
    try {
      setSelecionadas(await api.obterUnidadesGeridas(usuario.id));
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar.");
    } finally {
      setCarregando(false);
    }
  }

  function alternar(unidadeId: string) {
    setSelecionadas((atual) =>
      atual.includes(unidadeId) ? atual.filter((id) => id !== unidadeId) : [...atual, unidadeId],
    );
  }

  async function salvar() {
    setErro(null);
    try {
      await api.definirUnidadesGeridas(usuario.id, { unidade_ids: selecionadas });
      setAberto(false);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível salvar.");
    }
  }

  if (!aberto) {
    return (
      <button onClick={abrir} className="text-sm text-blue-600">
        Unidades geridas
      </button>
    );
  }

  return (
    <div className="text-sm">
      {carregando ? (
        <p>Carregando…</p>
      ) : (
        <div className="space-y-1">
          {unidades.map((u) => (
            <label key={u.id} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selecionadas.includes(u.id)}
                onChange={() => alternar(u.id)}
              />
              {u.nome}
            </label>
          ))}
          <div>
            <button onClick={salvar} className="text-blue-600">
              Salvar
            </button>
            <button onClick={() => setAberto(false)} className="ml-2 text-gray-500">
              Cancelar
            </button>
          </div>
        </div>
      )}
      {erro && <p className="text-red-600">{erro}</p>}
    </div>
  );
}

function AcaoResetarSenha({ usuario }: { usuario: Usuario }) {
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function resetar() {
    setErro(null);
    setMensagem(null);
    try {
      const resp = await api.resetarSenhaAdmin(usuario.id);
      setMensagem(resp.mensagem);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível resetar a senha.");
    }
  }

  return (
    <div>
      <button onClick={resetar} className="text-sm text-orange-600">
        Resetar senha
      </button>
      {mensagem && <p className="text-xs text-green-700">{mensagem}</p>}
      {erro && <p className="text-xs text-red-600">{erro}</p>}
    </div>
  );
}

function AcaoPermissaoAuditoria({ usuario, onAlterado }: { usuario: Usuario; onAlterado: () => void }) {
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function alternar() {
    setErro(null);
    setEnviando(true);
    try {
      if (usuario.pode_auditar) {
        await api.revogarPermissaoAuditoria(usuario.id);
      } else {
        await api.concederPermissaoAuditoria(usuario.id);
      }
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível alterar a permissão de auditoria.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div>
      <button onClick={alternar} disabled={enviando} className="text-sm text-purple-600 disabled:opacity-50">
        {usuario.pode_auditar ? "Revogar Permissão de Auditoria" : "Conceder Permissão de Auditoria"}
      </button>
      {erro && <p className="text-xs text-red-600">{erro}</p>}
    </div>
  );
}

function AcaoDesativarUsuario({ usuario, onAlterado }: { usuario: Usuario; onAlterado: () => void }) {
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (usuario.status === "inativo") return null;

  async function desativar() {
    setErro(null);
    setEnviando(true);
    try {
      await api.desativarUsuario(usuario.id);
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível desativar o usuário.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div>
      <button onClick={desativar} disabled={enviando} className="text-sm text-red-600 disabled:opacity-50">
        Desativar Usuário
      </button>
      {erro && <p className="text-xs text-red-600">{erro}</p>}
    </div>
  );
}

function AdminUsuariosConteudo() {
  const { usuario: usuarioAtual } = useAuth();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  async function carregar() {
    try {
      const [listaUsuarios, listaUnidades] = await Promise.all([api.listarUsuarios(), api.listarUnidades()]);
      setUsuarios(listaUsuarios.items);
      setUnidades(listaUnidades);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os usuários.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  if (!usuarioAtual) return null;
  const souAdministrador = usuarioAtual.perfil === "administrador";

  return (
    <div>
      <h1 className="text-2xl font-semibold">Usuários</h1>

      <div className="mt-4">
        <CadastroUsuarioForm unidades={unidades} perfilAtual={usuarioAtual.perfil as Perfil} onCriado={carregar} />
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b font-medium">
            <th className="p-2">Nome</th>
            <th className="p-2">E-mail</th>
            <th className="p-2">Perfil</th>
            <th className="p-2">Status</th>
            <th className="p-2">Unidade</th>
            <th className="p-2">Ações</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id} className="border-t align-top">
              <td className="p-2">{u.nome}</td>
              <td className="p-2">{u.email}</td>
              <td className="p-2 capitalize">{u.perfil}</td>
              <td className="p-2 capitalize">{u.status.replaceAll("_", " ")}</td>
              <td className="p-2">{nomeUnidade(unidades, u.unidade_id)}</td>
              <td className="space-y-1 p-2">
                {souAdministrador && u.perfil === "servidor" && (
                  <AcaoTransferirUnidade usuario={u} unidades={unidades} onAlterado={carregar} />
                )}
                {souAdministrador && u.perfil === "gestor" && (
                  <AcaoUnidadesGeridas usuario={u} unidades={unidades} />
                )}
                {souAdministrador && <AcaoResetarSenha usuario={u} />}
                {souAdministrador && <AcaoPermissaoAuditoria usuario={u} onAlterado={carregar} />}
                {souAdministrador && <AcaoDesativarUsuario usuario={u} onAlterado={carregar} />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminUsuariosPage() {
  return (
    <ProtectedShell>
      <AdminUsuariosConteudo />
    </ProtectedShell>
  );
}
