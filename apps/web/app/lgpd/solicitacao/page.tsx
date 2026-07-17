"use client";

import { useState } from "react";

import { ApiError, api } from "@/lib/api";

export default function SolicitacaoLgpdPage() {
  const [numeroProcesso, setNumeroProcesso] = useState("");
  const [nome, setNome] = useState("");
  const [cpf, setCpf] = useState("");
  const [email, setEmail] = useState("");
  const [tipo, setTipo] = useState<"exclusao" | "anonimizacao">("exclusao");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [protocolo, setProtocolo] = useState<string | null>(null);

  async function enviar(event: React.FormEvent) {
    event.preventDefault();
    if (!arquivo) {
      setErro("Anexe o documento de identificação.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      const resposta = await api.solicitarLgpd({
        numero_processo: numeroProcesso,
        nome,
        cpf,
        email,
        tipo,
        arquivo,
      });
      setProtocolo(resposta.protocolo);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível registrar a solicitação.");
    } finally {
      setEnviando(false);
    }
  }

  if (protocolo) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <h1 className="text-2xl font-semibold">Solicitação registrada</h1>
        <p className="mt-4 text-sm">
          Solicitação registrada com sucesso. Protocolo: <strong>{protocolo}</strong>. Você
          receberá a resposta no e-mail informado em até 15 dias.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="text-2xl font-semibold">Solicitação LGPD</h1>
      <p className="mt-1 text-sm text-gray-600">
        Titulares de dados pessoais (ou seus representantes legais) podem solicitar a exclusão
        ou anonimização de seus dados em um processo.
      </p>

      <form onSubmit={(e) => void enviar(e)} className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium" htmlFor="numero_processo">
            Número do processo
          </label>
          <input
            id="numero_processo"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={numeroProcesso}
            onChange={(e) => setNumeroProcesso(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium" htmlFor="nome">
            Nome completo
          </label>
          <input
            id="nome"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium" htmlFor="cpf">
            CPF
          </label>
          <input
            id="cpf"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={cpf}
            onChange={(e) => setCpf(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium" htmlFor="email">
            E-mail para resposta
          </label>
          <input
            id="email"
            type="email"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium" htmlFor="tipo">
            Tipo de solicitação
          </label>
          <select
            id="tipo"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={tipo}
            onChange={(e) => setTipo(e.target.value as "exclusao" | "anonimizacao")}
          >
            <option value="exclusao">Exclusão de dados</option>
            <option value="anonimizacao">Anonimização de dados</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium" htmlFor="arquivo">
            Documento de identificação (PDF, JPG ou PNG)
          </label>
          <input
            id="arquivo"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="mt-1 w-full text-sm"
            onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
            required
          />
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Enviando…" : "Enviar solicitação"}
        </button>
      </form>
    </div>
  );
}
