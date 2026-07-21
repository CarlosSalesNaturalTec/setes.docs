"use client";

// Gráfico de barras horizontais de distribuição (US 6.2, D4) — um hue de marca
// (navy) por barra, já que cada gráfico é uma única série (magnitude por
// categoria, não identidade). A tabela `sr-only` espelha os mesmos dados como
// alternativa acessível/textual ao SVG do recharts.
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { Schemas } from "@/lib/api";

type DistribuicaoItem = Schemas["DistribuicaoItem"];

const MSG_VAZIO = "Nenhum dado disponível para o período";
const COR_BARRA = "#2f5a8a"; // navy-600 (tailwind.config.ts)
const ALTURA_BARRA = 32;
const ALTURA_MINIMA = 96;

export function GraficoDistribuicao({
  titulo,
  itens,
}: {
  titulo: string;
  itens: DistribuicaoItem[];
}) {
  return (
    <section className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
      <h2 className="text-sm font-medium text-gray-700">{titulo}</h2>
      {itens.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">{MSG_VAZIO}</p>
      ) : (
        <>
          <div
            className="mt-2"
            style={{ width: "100%", height: Math.max(itens.length * ALTURA_BARRA, ALTURA_MINIMA) }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={itens} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
                <CartesianGrid horizontal={false} stroke="#eef2f8" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <YAxis
                  type="category"
                  dataKey="rotulo"
                  width={140}
                  tick={{ fontSize: 12 }}
                  stroke="#94a3b8"
                />
                <Tooltip />
                <Bar dataKey="quantidade" fill={COR_BARRA} radius={[0, 4, 4, 0]} maxBarSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <table className="sr-only">
            <caption>{titulo}</caption>
            <thead>
              <tr>
                <th>Rótulo</th>
                <th>Quantidade</th>
              </tr>
            </thead>
            <tbody>
              {itens.map((item) => (
                <tr key={item.rotulo}>
                  <td>{item.rotulo}</td>
                  <td>{item.quantidade}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
