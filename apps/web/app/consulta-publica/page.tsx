"use client";

import { useState } from "react";

import { ApiError, api, type Schemas } from "@/lib/api";
import { rotuloStatus } from "@/lib/processo-ui";

type ProcessoPublico = Schemas["ProcessoPublicoResponse"];
type ItemPesquisa = Schemas["ItemPesquisaPublicaResponse"];

function ResultadoProcesso({ processo }: { processo: ProcessoPublico }) {
  const interessados = processo.interessados ?? [];
  const historico = processo.historico ?? [];
  return (
    <div className="mt-6 rounded border p-4 text-sm">
      <p className="font-mono text-xs text-gray-500">{processo.numero}</p>
      <h2 className="mt-1 text-lg font-semibold">{processo.assunto}</h2>
      {/* Coluna única em viewport estreito, evitando compressão do valor (D4) */}
      <dl className="mt-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
        <dt className="text-gray-500">Tipo de processo</dt>
        <dd>{processo.tipo_processo}</dd>
        <dt className="text-gray-500">Status</dt>
        <dd>{rotuloStatus(processo.status)}</dd>
        <dt className="text-gray-500">Unidade atual</dt>
        <dd>{processo.unidade_atual}</dd>
        <dt className="text-gray-500">Criado em</dt>
        <dd>{new Date(processo.criado_em).toLocaleDateString("pt-BR")}</dd>
      </dl>

      {interessados.length > 0 && (
        <div className="mt-4">
          <h3 className="font-medium">Interessados</h3>
          <ul className="mt-1 list-disc pl-5">
            {interessados.map((interessado, i) => (
              <li key={i}>{interessado.nome}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4">
        <h3 className="font-medium">Histórico de movimentações</h3>
        {historico.length === 0 ? (
          <p className="mt-1 text-gray-500">Nenhuma movimentação registrada.</p>
        ) : (
          <ul className="mt-1 space-y-1">
            {historico.map((evento, i) => (
              <li key={i} className="text-gray-700">
                {new Date(evento.criado_em).toLocaleDateString("pt-BR")} —{" "}
                {evento.unidade_origem ?? "—"} → {evento.unidade_destino ?? "—"} (
                {rotuloStatus(evento.status_resultante)})
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function ConsultaPorNumero() {
  const [numero, setNumero] = useState("");
  const [processo, setProcesso] = useState<ProcessoPublico | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [consultando, setConsultando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setConsultando(true);
    setMensagem(null);
    setProcesso(null);
    try {
      const resultado = await api.consultarProcessoPublico(numero);
      setProcesso(resultado);
    } catch (err) {
      setMensagem(
        err instanceof ApiError ? err.detail : "Não foi possível consultar o processo.",
      );
    } finally {
      setConsultando(false);
    }
  }

  return (
    <section>
      <h2 className="text-lg font-semibold">Consultar por número</h2>
      <form onSubmit={onSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="numero" className="block text-sm">
            Número do processo
          </label>
          <input
            id="numero"
            type="text"
            placeholder="AAAA/NNNNNN"
            value={numero}
            onChange={(e) => setNumero(e.target.value)}
            required
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={consultando}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {consultando ? "Consultando…" : "Consultar"}
        </button>
      </form>

      {mensagem && <p className="mt-4 text-sm text-red-600">{mensagem}</p>}
      {processo && <ResultadoProcesso processo={processo} />}
    </section>
  );
}

function PesquisaProcessos() {
  const [assunto, setAssunto] = useState("");
  const [tipoProcesso, setTipoProcesso] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [pagina, setPagina] = useState(1);
  const [resultado, setResultado] = useState<Schemas["PesquisaPublicaResponse"] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [pesquisando, setPesquisando] = useState(false);

  async function pesquisar(paginaAlvo: number) {
    setPesquisando(true);
    setErro(null);
    try {
      const resp = await api.pesquisarProcessosPublico({
        assunto: assunto || undefined,
        tipo_processo: tipoProcesso || undefined,
        data_inicio: dataInicio || undefined,
        data_fim: dataFim || undefined,
        pagina: paginaAlvo,
      });
      setResultado(resp);
      setPagina(paginaAlvo);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível pesquisar os processos.");
      setResultado(null);
    } finally {
      setPesquisando(false);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    void pesquisar(1);
  }

  const totalPaginas = resultado ? Math.ceil(resultado.total / resultado.page_size) : 0;

  return (
    <section className="mt-10">
      <h2 className="text-lg font-semibold">Pesquisar por assunto, tipo ou período</h2>
      <form onSubmit={onSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="assunto" className="block text-sm">
            Assunto
          </label>
          <input
            id="assunto"
            type="text"
            value={assunto}
            onChange={(e) => setAssunto(e.target.value)}
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="tipo-processo" className="block text-sm">
            Tipo de processo
          </label>
          <input
            id="tipo-processo"
            type="text"
            value={tipoProcesso}
            onChange={(e) => setTipoProcesso(e.target.value)}
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="data-inicio" className="block text-sm">
            Data inicial
          </label>
          <input
            id="data-inicio"
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="data-fim" className="block text-sm">
            Data final
          </label>
          <input
            id="data-fim"
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="mt-1 rounded border px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={pesquisando}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {pesquisando ? "Pesquisando…" : "Pesquisar"}
        </button>
      </form>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}

      {resultado && resultado.items.length === 0 && (
        <p className="mt-4 text-sm text-gray-600">{resultado.mensagem_vazio}</p>
      )}

      {resultado && resultado.items.length > 0 && (
        <>
          <ul className="mt-4 space-y-2">
            {resultado.items.map((item: ItemPesquisa) => (
              <li key={item.numero} className="rounded border p-3 text-sm">
                <p className="font-mono text-xs text-gray-500">{item.numero}</p>
                <p className="font-medium">{item.assunto}</p>
                <p className="text-gray-600">
                  {item.tipo_processo} · {rotuloStatus(item.status)} · {item.unidade_atual}
                </p>
              </li>
            ))}
          </ul>

          {totalPaginas > 1 && (
            <div className="mt-4 flex items-center gap-3 text-sm">
              <button
                type="button"
                onClick={() => void pesquisar(pagina - 1)}
                disabled={pagina <= 1 || pesquisando}
                className="rounded border px-3 py-1 disabled:opacity-50"
              >
                Anterior
              </button>
              <span>
                Página {pagina} de {totalPaginas}
              </span>
              <button
                type="button"
                onClick={() => void pesquisar(pagina + 1)}
                disabled={pagina >= totalPaginas || pesquisando}
                className="rounded border px-3 py-1 disabled:opacity-50"
              >
                Próxima
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default function ConsultaPublicaPage() {
  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Consulta Pública de Processos</h1>
      <p className="mt-1 text-sm text-gray-600">
        Acompanhe o andamento de um processo, sem necessidade de login.
      </p>

      <div className="mt-6">
        <ConsultaPorNumero />
      </div>
      <PesquisaProcessos />
    </main>
  );
}
