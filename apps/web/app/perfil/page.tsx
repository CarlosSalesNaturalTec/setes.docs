"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { TrocarSenhaForm } from "@/components/trocar-senha-form";
import { ApiError, api, type Schemas } from "@/lib/api";

const NOME_MAX_LENGTH = 200;

function EditarNomeForm({
  nomeAtual,
  onSalvo,
}: {
  nomeAtual: string;
  onSalvo: (perfil: Schemas["MeuPerfilResponse"]) => void;
}) {
  const { recarregar } = useAuth();
  const [nome, setNome] = useState(nomeAtual);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState(false);

  useEffect(() => {
    setNome(nomeAtual);
  }, [nomeAtual]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(false);

    if (!nome.trim()) {
      setErro("Nome é obrigatório");
      return;
    }
    if (nome.length > NOME_MAX_LENGTH) {
      setErro(`Nome deve ter no máximo ${NOME_MAX_LENGTH} caracteres`);
      return;
    }

    setSalvando(true);
    try {
      const perfilAtualizado = await api.atualizarMeuPerfil({ nome });
      onSalvo(perfilAtualizado);
      await recarregar();
      setSucesso(true);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível salvar o nome.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-2 text-sm">
      <label htmlFor="nome" className="text-gray-500">
        Nome
      </label>
      <input
        id="nome"
        type="text"
        value={nome}
        maxLength={NOME_MAX_LENGTH}
        onChange={(e) => setNome(e.target.value)}
        className="rounded border px-3 py-2"
      />
      {erro && <p className="text-red-600">{erro}</p>}
      {sucesso && <p className="text-green-600">Nome atualizado com sucesso.</p>}
      <button
        type="submit"
        disabled={salvando}
        className="mt-1 w-fit rounded bg-gray-900 px-4 py-2 text-white disabled:opacity-50"
      >
        {salvando ? "Salvando…" : "Salvar nome"}
      </button>
    </form>
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

        <EditarNomeForm nomeAtual={perfil.usuario.nome} onSalvo={setPerfil} />
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
