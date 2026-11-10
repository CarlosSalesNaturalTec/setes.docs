"use client";

import type { Schemas } from "@/lib/api";

type Resultado = Schemas["ResultadoVerificacaoResponse"];
type Assinatura = Schemas["AssinaturaVerificada"];
type Veredito = Schemas["VereditoAssinatura"];

// Cor/ícone por veredito (change assinatura-verificacao-fundacao, D9): verde
// só para válida; âmbar para os vereditos que não afirmam validade plena;
// vermelho para inválida. O TEXTO vem sempre da API (D2) — aqui não se reescreve.
const ESTILO: Record<Veredito, { classe: string; icone: string; rotulo: string }> = {
  valida: { classe: "border-green-600 bg-green-50 text-green-800", icone: "✔", rotulo: "Válida" },
  alterada_apos_assinatura: {
    classe: "border-amber-500 bg-amber-50 text-amber-900",
    icone: "⚠",
    rotulo: "Atenção",
  },
  fora_icp_brasil: {
    classe: "border-amber-500 bg-amber-50 text-amber-900",
    icone: "⚠",
    rotulo: "Atenção",
  },
  inconclusiva: {
    classe: "border-amber-500 bg-amber-50 text-amber-900",
    icone: "?",
    rotulo: "Inconclusiva",
  },
  invalida: { classe: "border-red-600 bg-red-50 text-red-800", icone: "✖", rotulo: "Alerta" },
};

function formatarDataHora(iso: string): string {
  // Horário de Brasília (D6) — o mesmo offset fixo usado pelo backend.
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Sao_Paulo",
  }).format(new Date(iso));
}

function LinhaAssinatura({ assinatura }: { assinatura: Assinatura }) {
  const estilo = ESTILO[assinatura.veredito];
  return (
    <li className={`rounded border-l-4 p-2 ${estilo.classe}`} data-veredito={assinatura.veredito}>
      <p className="font-medium">
        <span aria-label={estilo.rotulo} role="img" className="mr-1">
          {estilo.icone}
        </span>
        {assinatura.mensagem}
      </p>
      <dl className="mt-1 grid grid-cols-1 gap-x-3 text-xs sm:grid-cols-[auto_1fr]">
        <dt className="font-medium">Signatário</dt>
        <dd className="break-words">
          {assinatura.signatario_nome ?? "não informado no certificado"}
        </dd>
        <dt className="font-medium">CPF</dt>
        <dd>{assinatura.signatario_cpf ?? "não informado no certificado"}</dd>
        <dt className="font-medium">Autoridade certificadora</dt>
        <dd className="break-words">
          {assinatura.autoridade_certificadora ?? "não informada no certificado"}
        </dd>
        <dt className="font-medium">Data/hora</dt>
        <dd>
          {assinatura.data_assinatura ? formatarDataHora(assinatura.data_assinatura) : "—"}{" "}
          {assinatura.origem_data === "carimbo"
            ? `(comprovada por carimbo de tempo${
                assinatura.autoridade_carimbo ? ` — ${assinatura.autoridade_carimbo}` : ""
              })`
            : "(declarada pelo signatário, sem carimbo de tempo)"}
        </dd>
      </dl>
    </li>
  );
}

export function PainelVerificacaoAssinatura({
  nomeDocumento,
  carregando,
  resultado,
  erro,
  onFechar,
}: {
  nomeDocumento: string;
  carregando: boolean;
  resultado: Resultado | null;
  erro: string | null;
  onFechar: () => void;
}) {
  return (
    <div
      role="region"
      aria-label={`Verificação de assinatura — ${nomeDocumento}`}
      className="mt-2 rounded border bg-white p-3 text-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium">Verificação de assinatura</h3>
        <button type="button" onClick={onFechar} className="rounded border px-2 py-0.5 text-xs">
          Fechar
        </button>
      </div>

      {carregando && <p className="mt-2 text-gray-600">Verificando assinatura…</p>}
      {erro && <p className="mt-2 text-red-600">{erro}</p>}

      {resultado && (
        <div className="mt-2 space-y-2">
          {resultado.situacao === "assinado" && resultado.resumo ? (
            <>
              {resultado.assinaturas.length > 1 && (
                <p
                  className={`rounded border-l-4 p-2 font-medium ${ESTILO[resultado.resumo].classe}`}
                  data-testid="resumo-verificacao"
                >
                  Resumo do documento: {resultado.mensagem_resumo}
                </p>
              )}
              <ol className="space-y-2">
                {resultado.assinaturas.map((a) => (
                  <LinhaAssinatura key={a.ordem} assinatura={a} />
                ))}
              </ol>
            </>
          ) : (
            <p className="text-gray-700">{resultado.mensagem_resumo}</p>
          )}

          {resultado.aviso_veredito_oficial && resultado.url_verificador_oficial && (
            <p className="text-xs text-gray-600">
              {resultado.aviso_veredito_oficial}{" "}
              <a
                href={resultado.url_verificador_oficial}
                target="_blank"
                rel="noopener noreferrer"
                className="text-navy-700 underline"
              >
                Abrir o verificador oficial do ITI
              </a>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
