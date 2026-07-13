"use client";

import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";
import { MENSAGEM_COMPLEXIDADE_SENHA, senhaAtendeComplexidade } from "@/lib/validacao";

function TrocarSenhaForm() {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setMensagem(null);

    if (!senhaAtendeComplexidade(novaSenha)) {
      setErro(MENSAGEM_COMPLEXIDADE_SENHA);
      return;
    }
    if (novaSenha !== confirmarSenha) {
      setErro("As senhas não coincidem.");
      return;
    }

    setEnviando(true);
    try {
      const resp = await api.trocarSenha({ senha_atual: senhaAtual, nova_senha: novaSenha });
      setMensagem(resp.mensagem);
      setSenhaAtual("");
      setNovaSenha("");
      setConfirmarSenha("");
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível trocar a senha.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="mt-8 rounded border p-4">
      <h2 className="text-lg font-medium">Trocar senha</h2>
      <form onSubmit={onSubmit} className="mt-4 max-w-sm space-y-3">
        <div>
          <label htmlFor="senha-atual" className="block text-sm">
            Senha atual
          </label>
          <input
            id="senha-atual"
            type="password"
            value={senhaAtual}
            onChange={(e) => setSenhaAtual(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="nova-senha" className="block text-sm">
            Nova senha
          </label>
          <input
            id="nova-senha"
            type="password"
            value={novaSenha}
            onChange={(e) => setNovaSenha(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="confirmar-nova-senha" className="block text-sm">
            Confirmar nova senha
          </label>
          <input
            id="confirmar-nova-senha"
            type="password"
            value={confirmarSenha}
            onChange={(e) => setConfirmarSenha(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}
        {mensagem && <p className="text-sm text-green-700">{mensagem}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Salvando…" : "Trocar senha"}
        </button>
      </form>
    </section>
  );
}

function PerfilConteudo() {
  const [perfil, setPerfil] = useState<Schemas["MeuPerfilResponse"] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        setPerfil(await api.meuPerfil());
      } catch (err) {
        setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar o perfil.");
      }
    })();
  }, []);

  if (erro) return <p className="text-sm text-red-600">{erro}</p>;
  if (!perfil) return <p className="text-sm text-gray-500">Carregando…</p>;

  const processos = perfil.processos ?? [];
  const documentosAssinados = perfil.documentos_assinados ?? [];

  return (
    <div>
      <h1 className="text-2xl font-semibold">Meu Perfil</h1>

      <section className="mt-4 rounded border p-4">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-gray-500">Nome</dt>
          <dd>{perfil.usuario.nome}</dd>
          <dt className="text-gray-500">E-mail</dt>
          <dd>{perfil.usuario.email}</dd>
          <dt className="text-gray-500">Perfil</dt>
          <dd className="capitalize">{perfil.usuario.perfil}</dd>
          <dt className="text-gray-500">Status</dt>
          <dd className="capitalize">{perfil.usuario.status.replaceAll("_", " ")}</dd>
        </dl>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-medium">Processos em que atuei</h2>
        {processos.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">{perfil.mensagem_processos}</p>
        ) : (
          <ul className="mt-2 text-sm">
            {processos.map((p, i) => (
              <li key={i}>{JSON.stringify(p)}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-medium">Documentos assinados</h2>
        {documentosAssinados.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">{perfil.mensagem_documentos}</p>
        ) : (
          <ul className="mt-2 text-sm">
            {documentosAssinados.map((d, i) => (
              <li key={i}>{JSON.stringify(d)}</li>
            ))}
          </ul>
        )}
      </section>

      <TrocarSenhaForm />
    </div>
  );
}

export default function PerfilPage() {
  return (
    <ProtectedShell>
      <PerfilConteudo />
    </ProtectedShell>
  );
}
