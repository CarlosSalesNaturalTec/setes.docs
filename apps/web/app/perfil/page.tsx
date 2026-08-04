"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { Tabs } from "@/components/tabs";
import { TrocarSenhaForm } from "@/components/trocar-senha-form";
import { ApiError, api, type Schemas } from "@/lib/api";

const NOME_MAX_LENGTH = 200;

// Abas da tela "Meu Perfil" (change perfil-em-abas, design D1): a aba ativa
// vive na query string `?aba=`; valor ausente ou desconhecido cai em "perfil".
const ABA_PADRAO = "perfil";
const IDS_ABAS = ["perfil", "senha", "processos", "assinados"] as const;
type IdAba = (typeof IDS_ABAS)[number];

function normalizarAba(valor: string | null): IdAba {
  return (IDS_ABAS as readonly string[]).includes(valor ?? "") ? (valor as IdAba) : ABA_PADRAO;
}

// Change migracao-regiao-us-central1 (tasks.md 6.6) — alinhado a
// TipoEventoTramitacao (db/models.py); "despacho"/"encaminhamento"/
// "recebimento" foram extintos pelo change tramitacao-manual.
const TIPO_ACAO_ROTULO: Record<string, string> = {
  criacao: "Criação",
  envio: "Envio",
  devolucao: "Devolução",
  reatribuicao: "Reatribuição",
  conclusao: "Conclusão",
  arquivamento_automatico: "Arquivamento automático",
  marcar_sigilo: "Marcação de sigilo",
  remover_sigilo: "Remoção de sigilo",
};

function rotuloTipoAcao(tipo: unknown): string {
  if (typeof tipo !== "string") return "";
  return TIPO_ACAO_ROTULO[tipo] ?? tipo.replaceAll("_", " ");
}

function formatarData(valor: unknown): string {
  if (typeof valor !== "string") return "";
  const data = new Date(valor);
  return Number.isNaN(data.getTime()) ? "" : data.toLocaleDateString("pt-BR");
}

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

function MeuPerfilAba({
  perfil,
  onSalvo,
}: {
  perfil: Schemas["MeuPerfilResponse"];
  onSalvo: (perfil: Schemas["MeuPerfilResponse"]) => void;
}) {
  return (
    <section className="rounded border p-4">
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="text-gray-500">Nome</dt>
        <dd>{perfil.usuario.nome}</dd>
        <dt className="text-gray-500">E-mail</dt>
        <dd>{perfil.usuario.email}</dd>
        <dt className="text-gray-500">Perfil</dt>
        <dd className="capitalize">{perfil.usuario.perfil}</dd>
        <dt className="text-gray-500">Status</dt>
        <dd className="capitalize">{perfil.usuario.status.replaceAll("_", " ")}</dd>
        {/* Campos vazios são omitidos — nunca renderizam "null" na tela. */}
        {perfil.unidade_nome && (
          <>
            <dt className="text-gray-500">Unidade</dt>
            <dd>{perfil.unidade_nome}</dd>
          </>
        )}
        {perfil.setor_nome && (
          <>
            <dt className="text-gray-500">Setor</dt>
            <dd>{perfil.setor_nome}</dd>
          </>
        )}
        {perfil.usuario.cargo && (
          <>
            <dt className="text-gray-500">Cargo</dt>
            <dd>{perfil.usuario.cargo}</dd>
          </>
        )}
        {perfil.usuario.telefone && (
          <>
            <dt className="text-gray-500">Telefone</dt>
            <dd>{perfil.usuario.telefone}</dd>
          </>
        )}
        {perfil.usuario.chefia_direta && (
          <>
            <dt className="text-gray-500">Chefia direta</dt>
            <dd>{perfil.usuario.chefia_direta}</dd>
          </>
        )}
      </dl>

      <EditarNomeForm nomeAtual={perfil.usuario.nome} onSalvo={onSalvo} />
    </section>
  );
}

function ProcessosAtuadosAba({ perfil }: { perfil: Schemas["MeuPerfilResponse"] }) {
  const processos = perfil.processos ?? [];

  if (processos.length === 0) {
    return <p className="text-sm text-gray-500">{perfil.mensagem_processos}</p>;
  }

  return (
    <ul className="divide-y rounded border text-sm">
      {processos.map((p, i) => {
        const item = p as Record<string, unknown>;
        const numero = typeof item.numero === "string" ? item.numero : "";
        const assunto = typeof item.assunto === "string" ? item.assunto : "";
        const acao = rotuloTipoAcao(item.tipo_acao);
        const data = formatarData(item.data_acao);
        return (
          <li key={i} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 px-3 py-2">
            <div>
              <span className="font-medium">{numero}</span>
              {assunto && <span className="text-gray-600"> — {assunto}</span>}
            </div>
            <div className="text-xs text-gray-500">
              {acao}
              {acao && data && " · "}
              {data}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

// Aba "Documentos assinados" (change perfil-em-abas, design D3; change
// ajustes-ui-admin, design D5): a assinatura digital (Épico 4) está fora do
// MVP. A aba explica isso em vez de mostrar uma lista vazia silenciosa, e
// orienta a solicitação do Certificado Digital ICP-Brasil como providência
// externa ao sistema — sem oferecer nenhum controle de assinatura.
function DocumentosAssinadosAba() {
  return (
    <p className="text-sm text-gray-500">
      A assinatura digital de documentos será disponibilizada em uma fase futura do produto. Para
      se preparar, solicite seu Certificado Digital ICP-Brasil junto a uma Autoridade
      Certificadora.
    </p>
  );
}

function PerfilConteudo() {
  const router = useRouter();
  const searchParams = useSearchParams();
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

  const abaAtiva = normalizarAba(searchParams.get("aba"));

  const selecionarAba = useCallback(
    (id: string) => {
      const params = new URLSearchParams(searchParams);
      params.set("aba", id);
      router.push(`/perfil?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  if (erro) return <p className="text-sm text-red-600">{erro}</p>;
  if (!perfil) return <p className="text-sm text-gray-500">Carregando…</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold">Meu Perfil</h1>

      <div className="mt-4">
        <Tabs
          aria-label="Meu Perfil"
          abaAtiva={abaAtiva}
          onSelecionar={selecionarAba}
          abas={[
            { id: "perfil", rotulo: "Meu perfil", conteudo: <MeuPerfilAba perfil={perfil} onSalvo={setPerfil} /> },
            { id: "senha", rotulo: "Trocar senha", conteudo: <TrocarSenhaForm /> },
            {
              id: "processos",
              rotulo: "Processos em que atuei",
              conteudo: <ProcessosAtuadosAba perfil={perfil} />,
            },
            { id: "assinados", rotulo: "Documentos assinados", conteudo: <DocumentosAssinadosAba /> },
          ]}
        />
      </div>
    </div>
  );
}

export default function PerfilPage() {
  return (
    <ProtectedShell>
      <Suspense fallback={<p className="p-4 text-sm text-gray-500">Carregando…</p>}>
        <PerfilConteudo />
      </Suspense>
    </ProtectedShell>
  );
}
