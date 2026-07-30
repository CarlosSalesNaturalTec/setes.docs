"use client";

import { useEffect, useState } from "react";

import { ApiError, api, type Schemas } from "@/lib/api";

type Unidade = Schemas["UnidadeResponse"];
type Setor = Schemas["SetorResponse"];
type Perfil = Schemas["CadastroUsuarioRequest"]["perfil"];

const MSG_SETOR_OBRIGATORIO = "Setor é obrigatório para o perfil Servidor.";

/**
 * Cadastro de usuário (D6) — extraído do índice de /admin/usuarios para ser
 * montado dentro do modal acionado por "Novo usuário". Sem mudança de contrato:
 * é reorganização de UI mais os campos novos (setor, telefone, cargo, chefia).
 */
export function CadastroUsuarioForm({
  unidades,
  perfilAtual,
  onCriado,
}: {
  unidades: Unidade[];
  perfilAtual: Perfil;
  // Recebe o e-mail cadastrado: quem monta o formulário fecha o modal e exibe
  // a confirmação — a mensagem não pode viver aqui, o form é desmontado junto.
  onCriado: (email: string) => void;
}) {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [perfil, setPerfil] = useState<Perfil>("servidor");
  const [unidadeId, setUnidadeId] = useState("");
  const [setorId, setSetorId] = useState("");
  const [setores, setSetores] = useState<Setor[]>([]);
  const [telefone, setTelefone] = useState("");
  const [cargo, setCargo] = useState("");
  const [chefiaDireta, setChefiaDireta] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Gestor só pode cadastrar Servidor (US 1.2 Cen.3) — nem oferece a opção.
  const perfisPermitidos: Perfil[] =
    perfilAtual === "administrador" ? ["servidor", "gestor", "administrador"] : ["servidor"];
  const setorObrigatorio = perfil === "servidor";

  // Cascata Unidade → Setor: trocar a unidade limpa o setor e recarrega a
  // lista, que traz apenas os setores **ativos** da unidade escolhida.
  useEffect(() => {
    setSetorId("");
    if (!unidadeId) {
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
  }, [unidadeId]);

  function limpar() {
    setNome("");
    setEmail("");
    setPerfil("servidor");
    setUnidadeId("");
    setSetorId("");
    setTelefone("");
    setCargo("");
    setChefiaDireta("");
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    if (setorObrigatorio && !setorId) {
      setErro(MSG_SETOR_OBRIGATORIO);
      return;
    }

    setEnviando(true);
    try {
      await api.cadastrarUsuario({
        nome,
        email,
        perfil,
        unidade_id: unidadeId || null,
        setor_id: setorId || null,
        telefone: telefone || null,
        cargo: cargo || null,
        chefia_direta: chefiaDireta || null,
      });
      limpar();
      onCriado(email);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível cadastrar o usuário.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div>
        <label htmlFor="nome" className="block text-sm">
          Nome
        </label>
        <input
          id="nome"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          required
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
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
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
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
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
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
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
        >
          <option value="">(nenhuma)</option>
          {unidades.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nome}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="setor" className="block text-sm">
          Setor{setorObrigatorio && <span className="text-red-600"> *</span>}
        </label>
        <select
          id="setor"
          value={setorId}
          onChange={(e) => setSetorId(e.target.value)}
          disabled={!unidadeId}
          className="mt-1 w-full rounded border px-3 py-2 text-sm disabled:bg-gray-100"
        >
          <option value="">{unidadeId ? "(nenhum)" : "Selecione a unidade primeiro"}</option>
          {setores.map((s) => (
            <option key={s.id} value={s.id}>
              {s.nome} ({s.sigla})
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="telefone" className="block text-sm">
          Telefone
        </label>
        <input
          id="telefone"
          value={telefone}
          onChange={(e) => setTelefone(e.target.value)}
          maxLength={30}
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="cargo" className="block text-sm">
          Cargo
        </label>
        <input
          id="cargo"
          value={cargo}
          onChange={(e) => setCargo(e.target.value)}
          maxLength={200}
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="chefia-direta" className="block text-sm">
          Chefia direta
        </label>
        <input
          id="chefia-direta"
          value={chefiaDireta}
          onChange={(e) => setChefiaDireta(e.target.value)}
          maxLength={200}
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
        />
        {/* Texto livre: a chefia pode não ter conta no sistema (D4). */}
        <p className="mt-1 text-xs text-gray-500">Pode ser alguém sem conta no sistema.</p>
      </div>
      <div className="sm:col-span-2">
        <button
          type="submit"
          disabled={enviando}
          className="rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Salvando…" : "Cadastrar usuário"}
        </button>
        {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
      </div>
    </form>
  );
}
