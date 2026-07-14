"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, api } from "@/lib/api";
import { MENSAGEM_COMPLEXIDADE_SENHA, senhaAtendeComplexidade } from "@/lib/validacao";

export default function SetupPage() {
  const router = useRouter();
  const [verificando, setVerificando] = useState(true);
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [unidadeNome, setUnidadeNome] = useState("");
  const [unidadeSigla, setUnidadeSigla] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const status = await api.setupStatus();
        if (status.inicializado) {
          router.replace("/login");
          return;
        }
      } finally {
        setVerificando(false);
      }
    })();
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    if (!senhaAtendeComplexidade(senha)) {
      setErro(MENSAGEM_COMPLEXIDADE_SENHA);
      return;
    }
    if (senha !== confirmarSenha) {
      setErro("As senhas não coincidem.");
      return;
    }

    setEnviando(true);
    try {
      await api.setup({
        administrador: { nome, email, senha },
        unidade: { nome: unidadeNome, sigla: unidadeSigla },
      });
      router.push("/login?motivo=setup-concluido");
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Falha ao inicializar o sistema.");
    } finally {
      setEnviando(false);
    }
  }

  if (verificando) {
    return <p className="p-8 text-sm text-gray-500">Verificando…</p>;
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="text-2xl font-semibold">Inicialização do SETES.DOCS</h1>
      <p className="mt-2 text-sm text-gray-600">
        Este formulário só fica disponível antes do primeiro uso do sistema. Crie o Administrador
        root e a primeira unidade administrativa.
      </p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <fieldset className="space-y-3 rounded border p-4">
          <legend className="px-1 text-sm font-medium">Administrador</legend>
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
            <label htmlFor="senha" className="block text-sm">
              Senha
            </label>
            <input
              id="senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="confirmar-senha" className="block text-sm">
              Confirmar senha
            </label>
            <input
              id="confirmar-senha"
              type="password"
              value={confirmarSenha}
              onChange={(e) => setConfirmarSenha(e.target.value)}
              required
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
            />
          </div>
        </fieldset>

        <fieldset className="space-y-3 rounded border p-4">
          <legend className="px-1 text-sm font-medium">Primeira unidade administrativa</legend>
          <div>
            <label htmlFor="unidade-nome" className="block text-sm">
              Nome da unidade
            </label>
            <input
              id="unidade-nome"
              value={unidadeNome}
              onChange={(e) => setUnidadeNome(e.target.value)}
              required
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="unidade-sigla" className="block text-sm">
              Sigla
            </label>
            <input
              id="unidade-sigla"
              value={unidadeSigla}
              onChange={(e) => setUnidadeSigla(e.target.value)}
              required
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
            />
          </div>
        </fieldset>

        {erro && <p className="text-sm text-red-600">{erro}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="w-full rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Inicializando…" : "Inicializar sistema"}
        </button>
      </form>
    </main>
  );
}
