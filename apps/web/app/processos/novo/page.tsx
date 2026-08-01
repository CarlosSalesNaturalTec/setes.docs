"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EditorFormatado } from "@/components/editor-formatado";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type TipoProcesso = Schemas["TipoProcessoResponse"];
type Interessado = Schemas["InteressadoInput"];
type Modelo = Schemas["ModeloResponse"];

// Máscara leve de CPF/CNPJ conforme o tipo escolhido (validação real é no backend).
function mascarar(valor: string, tipo: "cpf" | "cnpj"): string {
  const d = valor.replace(/\D/g, "").slice(0, tipo === "cpf" ? 11 : 14);
  if (tipo === "cpf") {
    return d
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  }
  return d
    .replace(/(\d{2})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1/$2")
    .replace(/(\d{4})(\d{1,2})$/, "$1-$2");
}

function LinhaInteressado({
  interessado,
  onChange,
  onRemover,
}: {
  interessado: Interessado;
  onChange: (i: Interessado) => void;
  onRemover: () => void;
}) {
  const tipoDoc = (interessado.tipo_documento ?? "cpf") as "cpf" | "cnpj";
  return (
    <div className="grid grid-cols-1 gap-2 rounded border p-3 sm:grid-cols-[1fr_auto_1fr_auto_auto]">
      <input
        aria-label="Nome do interessado"
        placeholder="Nome completo"
        value={interessado.nome}
        onChange={(e) => onChange({ ...interessado, nome: e.target.value })}
        className="rounded border px-2 py-1 text-sm"
      />
      <select
        aria-label="Tipo de documento"
        value={tipoDoc}
        onChange={(e) =>
          onChange({ ...interessado, tipo_documento: e.target.value as "cpf" | "cnpj", documento: "" })
        }
        className="rounded border px-2 py-1 text-sm"
      >
        <option value="cpf">CPF</option>
        <option value="cnpj">CNPJ</option>
      </select>
      <input
        aria-label="Documento do interessado"
        placeholder={tipoDoc === "cpf" ? "000.000.000-00" : "00.000.000/0000-00"}
        value={interessado.documento ?? ""}
        onChange={(e) => onChange({ ...interessado, documento: mascarar(e.target.value, tipoDoc) })}
        className="rounded border px-2 py-1 text-sm"
      />
      <select
        aria-label="Tipo de participação"
        value={interessado.tipo_participacao ?? ""}
        onChange={(e) =>
          onChange({
            ...interessado,
            tipo_participacao: (e.target.value || null) as Interessado["tipo_participacao"],
          })
        }
        className="rounded border px-2 py-1 text-sm"
      >
        <option value="">Participação…</option>
        <option value="requerente">Requerente</option>
        <option value="representado">Representado</option>
        <option value="terceiro">Terceiro</option>
      </select>
      <button type="button" onClick={onRemover} className="text-sm text-red-600">
        remover
      </button>
    </div>
  );
}

function NovoProcessoConteudo() {
  const router = useRouter();
  const [tipos, setTipos] = useState<TipoProcesso[]>([]);
  const [assunto, setAssunto] = useState("");
  const [tipoId, setTipoId] = useState("");
  const [prazoDias, setPrazoDias] = useState("");
  const [interessados, setInteressados] = useState<Interessado[]>([]);
  const [modelos, setModelos] = useState<Modelo[]>([]);
  const [modeloId, setModeloId] = useState("");
  const [conteudoModelo, setConteudoModelo] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [erroCampos, setErroCampos] = useState<{ assunto?: string; tipo?: string; prazo?: string }>({});
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        setTipos(await api.listarTiposProcesso());
      } catch (err) {
        setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os tipos.");
      }
    })();
    void (async () => {
      try {
        setModelos(await api.listarModelos(true));
      } catch {
        // Catálogo de modelos é opcional na criação do processo — falha ao
        // carregar não deve bloquear o fluxo sem modelo.
      }
    })();
  }, []);

  function selecionarModelo(id: string) {
    setModeloId(id);
    const modelo = modelos.find((m) => m.id === id);
    setConteudoModelo(modelo ? modelo.conteudo : "");
  }

  function validar(): boolean {
    const e: typeof erroCampos = {};
    if (!assunto.trim()) e.assunto = "Informe o assunto.";
    if (!tipoId) e.tipo = "Selecione o tipo de processo.";
    if (!prazoDias || Number(prazoDias) <= 0) e.prazo = "Informe um prazo em dias.";
    setErroCampos(e);
    return Object.keys(e).length === 0;
  }

  async function onSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    setErro(null);
    if (!validar()) return;
    setEnviando(true);
    try {
      const proc = await api.criarProcesso({
        assunto,
        tipo_processo_id: tipoId,
        prazo_dias: Number(prazoDias),
        interessados: interessados.filter((i) => i.nome.trim()),
      });
      if (modeloId) {
        try {
          await api.gerarDocumento(proc.id, { modelo_id: modeloId, conteudo: conteudoModelo });
        } catch (err) {
          setErro(
            err instanceof ApiError
              ? `Processo criado, mas o documento não pôde ser gerado: ${err.detail}`
              : "Processo criado, mas o documento não pôde ser gerado.",
          );
        }
      }
      router.push(`/processos/${proc.id}`);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível criar o processo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Novo processo</h1>
      <form
        onSubmit={onSubmit}
        className="mt-4 space-y-4 rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card"
      >
        <div>
          <label htmlFor="assunto" className="block text-sm">
            Assunto
          </label>
          <input
            id="assunto"
            value={assunto}
            onChange={(e) => setAssunto(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
          {erroCampos.assunto && <p className="mt-1 text-sm text-red-600">{erroCampos.assunto}</p>}
        </div>

        <div>
          <label htmlFor="tipo" className="block text-sm">
            Tipo de processo
          </label>
          <select
            id="tipo"
            value={tipoId}
            onChange={(e) => setTipoId(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          >
            <option value="">Selecione…</option>
            {tipos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
          {erroCampos.tipo && <p className="mt-1 text-sm text-red-600">{erroCampos.tipo}</p>}
        </div>

        <div>
          <label htmlFor="prazo" className="block text-sm">
            Prazo (dias corridos)
          </label>
          <input
            id="prazo"
            type="number"
            min={1}
            value={prazoDias}
            onChange={(e) => setPrazoDias(e.target.value)}
            className="mt-1 w-40 rounded border px-3 py-2 text-sm"
          />
          {erroCampos.prazo && <p className="mt-1 text-sm text-red-600">{erroCampos.prazo}</p>}
        </div>

        <div>
          <label htmlFor="modelo" className="block text-sm">
            Modelo de documento (opcional)
          </label>
          <select
            id="modelo"
            value={modeloId}
            onChange={(e) => selecionarModelo(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          >
            <option value="">Nenhum — começar do zero</option>
            {modelos.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nome}
              </option>
            ))}
          </select>
          {modeloId && (
            <div className="mt-2">
              <EditorFormatado
                key={modeloId}
                valorInicial={conteudoModelo}
                onChange={setConteudoModelo}
                ariaLabel="Conteúdo do documento a gerar"
              />
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium">Interessados</h2>
            <button
              type="button"
              onClick={() => setInteressados([...interessados, { nome: "", tipo_documento: "cpf" }])}
              className="text-sm text-navy-600"
            >
              Adicionar interessado
            </button>
          </div>
          <div className="mt-2 space-y-2">
            {interessados.map((i, idx) => (
              <LinhaInteressado
                key={idx}
                interessado={i}
                onChange={(novo) =>
                  setInteressados(interessados.map((x, j) => (j === idx ? novo : x)))
                }
                onRemover={() => setInteressados(interessados.filter((_, j) => j !== idx))}
              />
            ))}
            {interessados.length === 0 && (
              <p className="text-sm text-gray-500">Nenhum interessado adicionado.</p>
            )}
          </div>
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Criando…" : "Criar processo"}
        </button>
      </form>
    </div>
  );
}

export default function NovoProcessoPage() {
  return (
    <ProtectedShell>
      <NovoProcessoConteudo />
    </ProtectedShell>
  );
}
