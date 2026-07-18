"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import { rotaInicial } from "@/lib/rota-inicial";

export default function Home() {
  const router = useRouter();
  const { usuario, carregando } = useAuth();

  useEffect(() => {
    if (carregando) return;
    if (usuario) {
      router.replace(rotaInicial(usuario));
      return;
    }
    void (async () => {
      try {
        const status = await api.setupStatus();
        router.replace(status.inicializado ? "/login" : "/setup");
      } catch {
        router.replace("/login");
      }
    })();
  }, [carregando, usuario, router]);

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">SETES.DOCS</h1>
      <p className="mt-2 text-gray-600">Carregando…</p>
    </main>
  );
}
