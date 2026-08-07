import { createContext, useContext, useEffect, useState, useCallback } from "react";

import * as authService from "../services/auth";
import { setTokens, clearTokens, hasTokens } from "../lib/tokenStorage";
import { setOnSessionExpired } from "../lib/apiClient";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // `loading` cobre a validação inicial da sessão (checar /me se há tokens).
  const [loading, setLoading] = useState(true);

  // Limpa a sessão local. Usado no logout e quando o refresh expira em definitivo.
  const clearSession = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  // Quando o apiClient não consegue renovar o token, ele chama isto: derruba o
  // estado local e a ProtectedRoute cuida do redirect (sem acoplar o router aqui).
  useEffect(() => {
    setOnSessionExpired(() => setUser(null));
  }, []);

  // Na carga inicial: se há tokens guardados, valida-os buscando o /me.
  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!hasTokens()) {
        setLoading(false);
        return;
      }
      try {
        const me = await authService.getMe();
        if (active) {
          setUser(me);
        }
      } catch {
        // Tokens inválidos/expirados e sem refresh possível: começa deslogado.
        if (active) {
          clearSession();
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, [clearSession]);

  const login = useCallback(async ({ email, password }) => {
    const tokens = await authService.login({ email, password });
    setTokens(tokens);
    const me = await authService.getMe();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (payload) => {
    // Não autentica: a API não emite tokens no cadastro.
    return authService.register(payload);
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    clearSession();
  }, [clearSession]);

  const value = {
    user,
    isAuthenticated: Boolean(user),
    loading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
