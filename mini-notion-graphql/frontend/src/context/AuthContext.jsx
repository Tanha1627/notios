import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../api/graphql";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("notio_token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await api.me(token);
        if (!cancelled) setUser(data.me);
      } catch {
        if (!cancelled) {
          setToken(null);
          localStorage.removeItem("notio_token");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (email, password) => {
    const data = await api.login({ email, password });
    localStorage.setItem("notio_token", data.login.token);
    setToken(data.login.token);
    setUser(data.login.user);
    return data.login.user;
  }, []);

  const register = useCallback(async (email, name, password) => {
    const data = await api.register({ email, name, password });
    localStorage.setItem("notio_token", data.register.token);
    setToken(data.register.token);
    setUser(data.register.user);
    return data.register.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("notio_token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
