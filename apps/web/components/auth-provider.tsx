"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, type Schemas } from "@/lib/api";
import { getToken, setToken, subscribeToken } from "@/lib/session-store";

type Usuario = Schemas["UsuarioResumo"];

interface AuthContextValue {
  usuario: Usuario | null;
  token: string | null;
  carregando: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => Promise<void>;
  recarregar: () => Promise<void>;
  /** Estabelece a sessão a partir de uma LoginResponse já obtida fora de
   * `login()` (ex.: primeiro acesso) — evita duplicar a chamada de rede. */
  definirSessao: (usuario: Usuario, token: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  const carregarUsuario = useCallback(async () => {
    if (!getToken()) {
      setUsuario(null);
      setCarregando(false);
      return;
    }
    try {
      const resp = await api.me();
      setUsuario(resp.usuario);
    } catch {
      setToken(null);
      setUsuario(null);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    setTokenState(getToken());
    void carregarUsuario();
    return subscribeToken(() => setTokenState(getToken()));
  }, [carregarUsuario]);

  const login = useCallback(async (email: string, senha: string) => {
    const resp = await api.login({ email, senha });
    setToken(resp.token);
    setUsuario(resp.usuario);
  }, []);

  const definirSessao = useCallback((usuarioResp: Usuario, tokenResp: string) => {
    setToken(tokenResp);
    setUsuario(usuarioResp);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // encerra localmente mesmo que a chamada de rede falhe
    }
    setToken(null);
    setUsuario(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ usuario, token, carregando, login, logout, recarregar: carregarUsuario, definirSessao }),
    [usuario, token, carregando, login, logout, carregarUsuario, definirSessao],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  return ctx;
}
