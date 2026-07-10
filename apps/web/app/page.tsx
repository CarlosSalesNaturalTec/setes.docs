import { apiHealthPath } from "@/lib/api";

export default function Home() {
  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">SETES.DOCS</h1>
      <p className="mt-2 text-gray-600">
        Bootstrap da infraestrutura concluído. Frontend Next.js no ar.
      </p>
      <p className="mt-4 text-sm text-gray-500">
        Contrato da API (health): <code>{apiHealthPath}</code>
      </p>
    </main>
  );
}
