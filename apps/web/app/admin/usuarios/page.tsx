"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { CadastroUsuarioForm } from "@/components/cadastro-usuario-form";
import { IconButton } from "@/components/icon-button";
import { IconBuildings, IconKey, IconShield, IconTransfer, IconUserMinus } from "@/components/icons";
import { Modal } from "@/components/modal";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Unidade = Schemas["UnidadeResponse"];
type Usuario = Schemas["UsuarioResponse"];
type Perfil = Schemas["CadastroUsuarioRequest"]["perfil"];

// Filtro por nome é aplicado no backend (D5); o debounce evita uma requisição
// por tecla digitada.
const DEBOUNCE_FILTRO_MS = 300;

function nomeUnidade(unidades: Unidade[], unidadeId: string | null): string {
  if (!unidadeId) return "—";
  return unidades.find((u) => u.id === unidadeId)?.nome ?? unidadeId;
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
  const [setorId, setSetorId] = useState("");
  const [setores, setSetores] = useState<Schemas["SetorResponse"][]>([]);
  const [erro, setErro] = useState<string | null>(null);

  // A transferência exige um setor da nova unidade (D2) — a cascata carrega
  // apenas os setores ativos da unidade escolhida.
  useEffect(() => {
    setSetorId("");
    if (!aberto || !unidadeId) {
      setSetores([]);
      return;
    }
    let cancelado = false;
    void (async () => {
      try {
        const lista = await api.listarSetores(unidadeId, true);
        if (!cancelado) setSetores(lista);
      } catch {
        if (!cancelado) setSetores([]);
      }
    })();
    return () => {
      cancelado = true;
    };
  }, [aberto, unidadeId]);

  async function confirmar() {
    setErro(null);
    try {
      await api.transferirUnidade(usuario.id, { unidade_id: unidadeId, setor_id: setorId || null });
      setAberto(false);
      onAlterado();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível transferir.");
    }
  }

  if (!aberto) {
    return (
      <IconButton label="Transferir unidade" onClick={() => setAberto(true)} className="text-navy-600">
        <IconTransfer />
      </IconButton>
    );
  }

  return (
    <div className="space-y-1 text-sm">
      <select value={unidadeId} onChange={(e) => setUnidadeId(e.target.value)} className="rounded border px-2 py-1">
        <option value="">Selecione a unidade…</option>
        {unidades.map((u) => (
          <option key={u.id} value={u.id}>
            {u.nome}
          </option>
        ))}
      </select>
      <select
        value={setorId}
        onChange={(e) => setSetorId(e.target.value)}
        disabled={!unidadeId}
        aria-label="Setor de destino"
        className="rounded border px-2 py-1 disabled:bg-gray-100"
      >
        <option value="">Selecione o setor…</option>
        {setores.map((s) => (
          <option key={s.id} value={s.id}>
            {s.nome} ({s.sigla})
          </option>
        ))}
      </select>
      <div>
        <button onClick={confirmar} className="text-navy-600">
          Confirmar
        </button>
        <button onClick={() => setAberto(false)} className="ml-2 text-gray-500">
          Cancelar
        </button>
      </div>
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
      <IconButton label="Unidades geridas" onClick={abrir} className="text-navy-600">
        <IconBuildings />
      </IconButton>
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
            <button onClick={salvar} className="text-navy-600">
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
      <IconButton label="Resetar senha" onClick={resetar} className="text-orange-600">
        <IconKey />
      </IconButton>
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
      <IconButton
        label={usuario.pode_auditar ? "Revogar Permissão de Auditoria" : "Conceder Permissão de Auditoria"}
        onClick={alternar}
        disabled={enviando}
        className="text-purple-600"
      >
        <IconShield />
      </IconButton>
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
      <IconButton label="Desativar Usuário" onClick={desativar} disabled={enviando} className="text-red-600">
        <IconUserMinus />
      </IconButton>
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
  const [filtroNome, setFiltroNome] = useState("");
  const [filtroAplicado, setFiltroAplicado] = useState("");
  const [modalAberto, setModalAberto] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  async function carregar(nome = filtroAplicado) {
    try {
      const [listaUsuarios, listaUnidades] = await Promise.all([
        api.listarUsuarios(1, nome),
        api.listarUnidades(),
      ]);
      setUsuarios(listaUsuarios.items);
      setUnidades(listaUnidades);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os usuários.");
    } finally {
      setCarregando(false);
    }
  }

  // Debounce de 300 ms sobre o que foi digitado (D5) — a busca em si roda no
  // backend, então a lista filtra sem recarregar a página.
  useEffect(() => {
    const id = setTimeout(() => setFiltroAplicado(filtroNome), DEBOUNCE_FILTRO_MS);
    return () => clearTimeout(id);
  }, [filtroNome]);

  useEffect(() => {
    void carregar(filtroAplicado);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroAplicado]);

  if (!usuarioAtual) return null;
  const souAdministrador = usuarioAtual.perfil === "administrador";
  // Selects de atribuição só oferecem unidades ativas; a lista cheia fica
  // reservada ao lookup de nome na tabela (usuário pode exibir unidade extinta).
  const unidadesAtivas = unidades.filter((u) => u.ativo);

  return (
    <div>
      <h1 className="text-2xl font-semibold">Usuários</h1>

      {/* O espaço antes ocupado pelo formulário inline recebe o filtro (D5/D6). */}
      <div className="mt-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <label htmlFor="filtro-nome" className="block text-sm">
            Filtrar por nome
          </label>
          <input
            id="filtro-nome"
            value={filtroNome}
            onChange={(e) => setFiltroNome(e.target.value)}
            placeholder="Digite parte do nome…"
            className="mt-1 w-64 rounded border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="button"
          onClick={() => {
            setMensagemSucesso(null);
            setModalAberto(true);
          }}
          className="rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white"
        >
          Novo usuário
        </button>
      </div>

      <Modal titulo="Novo usuário" aberto={modalAberto} onFechar={() => setModalAberto(false)}>
        <CadastroUsuarioForm
          unidades={unidadesAtivas}
          perfilAtual={usuarioAtual.perfil as Perfil}
          onCriado={(email) => {
            // O modal fecha ao salvar, então a confirmação é exibida aqui —
            // dentro do formulário ela seria desmontada junto com o modal.
            setModalAberto(false);
            setMensagemSucesso(
              `Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${email}.`,
            );
            void carregar();
          }}
        />
      </Modal>

      {mensagemSucesso && <p className="mt-4 text-sm text-green-700">{mensagemSucesso}</p>}

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      <table className="mt-6 w-full overflow-hidden rounded-card border border-navy-50 text-left text-sm shadow-card">
        <thead>
          <tr className="border-b bg-gray-50 text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="px-3 py-2">Nome</th>
            <th className="px-3 py-2">E-mail</th>
            <th className="px-3 py-2">Perfil</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Unidade</th>
            <th className="px-3 py-2">Ações</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id} className="border-t align-top odd:bg-white even:bg-gray-50/50 hover:bg-navy-50/50">
              <td className="px-3 py-2">{u.nome}</td>
              <td className="px-3 py-2">{u.email}</td>
              <td className="px-3 py-2 capitalize">{u.perfil}</td>
              <td className="px-3 py-2 capitalize">{u.status.replaceAll("_", " ")}</td>
              <td className="px-3 py-2">
                {nomeUnidade(unidades, u.unidade_id)}
                {/* Servidores anteriores ao Setor ficam sem vínculo: a tela
                    sinaliza para regularização (design.md Risks). */}
                {u.perfil === "servidor" && !u.setor_id && (
                  <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800">
                    sem setor
                  </span>
                )}
              </td>
              <td className="px-3 py-2">
                <div className="flex flex-wrap items-center gap-1">
                  {souAdministrador && u.perfil === "servidor" && (
                    <AcaoTransferirUnidade usuario={u} unidades={unidadesAtivas} onAlterado={carregar} />
                  )}
                  {souAdministrador && u.perfil === "gestor" && (
                    <AcaoUnidadesGeridas usuario={u} unidades={unidadesAtivas} />
                  )}
                  {souAdministrador && <AcaoResetarSenha usuario={u} />}
                  {souAdministrador && <AcaoPermissaoAuditoria usuario={u} onAlterado={carregar} />}
                  {souAdministrador && <AcaoDesativarUsuario usuario={u} onAlterado={carregar} />}
                </div>
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
