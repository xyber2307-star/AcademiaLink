import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { User } from "../types";
import { authService, type LoginPayload, type RegisterPayload } from "../services/authService";

interface AuthContextValue {
  user: User | null;
  login: (p: LoginPayload) => Promise<User>;
  loginWithGoogle: () => Promise<User>;
  register: (p: RegisterPayload) => Promise<User>;
  verifyEmail: (code: string) => Promise<User | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => authService.getCurrentUser());

  const login = useCallback(async (p: LoginPayload) => { const u = await authService.login(p); setUser(u); return u; }, []);
  const loginWithGoogle = useCallback(async () => { const u = await authService.loginWithGoogle(); setUser(u); return u; }, []);
  const register = useCallback(async (p: RegisterPayload) => { const u = await authService.register(p); setUser(u); return u; }, []);
  const verifyEmail = useCallback(async (code: string) => { const u = await authService.verifyEmail(code); setUser(u); return u; }, []);
  const logout = useCallback(() => { authService.logout(); setUser(null); }, []);

  const value = useMemo(() => ({ user, login, loginWithGoogle, register, verifyEmail, logout }), [user, login, loginWithGoogle, register, verifyEmail, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
