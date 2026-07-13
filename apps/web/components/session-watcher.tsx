"use client";

// Timer de inatividade (US 1.8 Cen.2/2b) — aviso 2 min antes do timeout, com
// "Continuar Sessão" (renova via qualquer chamada autenticada — sliding
// window, D1) e "Sair" (logout imediato). Expiração automática ao vencer.
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { decodeJwtExp, getToken } from "@/lib/session-store";
import { useAuth } from "./auth-provider";

const AVISO_ANTES_MS = 2 * 60 * 1000;

export function SessionWatcher() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const [mostrarAviso, setMostrarAviso] = useState(false);
  const avisoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const expiraTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function limpar() {
      if (avisoTimer.current) clearTimeout(avisoTimer.current);
      if (expiraTimer.current) clearTimeout(expiraTimer.current);
    }

    limpar();
    setMostrarAviso(false);

    const atual = getToken();
    if (!atual) return limpar;

    const expSec = decodeJwtExp(atual);
    if (expSec === null) return limpar;

    const expiraEmMs = expSec * 1000 - Date.now();
    if (expiraEmMs <= 0) return limpar;

    const avisoEmMs = expiraEmMs - AVISO_ANTES_MS;
    if (avisoEmMs > 0) {
      avisoTimer.current = setTimeout(() => setMostrarAviso(true), avisoEmMs);
    } else {
      setMostrarAviso(true);
    }

    expiraTimer.current = setTimeout(() => {
      void (async () => {
        await logout();
        router.replace("/login?motivo=inatividade");
      })();
    }, expiraEmMs);

    return limpar;
  }, [token, logout, router]);

  async function continuarSessao() {
    try {
      await api.me(); // qualquer chamada autenticada renova a sessão (sliding window)
      setMostrarAviso(false);
    } catch {
      await logout();
      router.replace("/login?motivo=inatividade");
    }
  }

  async function sairAgora() {
    setMostrarAviso(false);
    await logout();
    router.replace("/login");
  }

  if (!mostrarAviso) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-lg font-semibold">Sua sessão está prestes a expirar</h2>
        <p className="mt-2 text-sm text-gray-600">
          Por inatividade, você será desconectado em breve. Deseja continuar conectado?
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={sairAgora} className="rounded border px-3 py-1.5 text-sm">
            Sair
          </button>
          <button
            type="button"
            onClick={continuarSessao}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white"
          >
            Continuar Sessão
          </button>
        </div>
      </div>
    </div>
  );
}
