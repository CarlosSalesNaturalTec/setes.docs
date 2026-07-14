"use client";

import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { TrocarSenhaForm } from "@/components/trocar-senha-form";
import { ApiError, api, type Schemas } from "@/lib/api";

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
