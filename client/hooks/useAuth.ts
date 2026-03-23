"use client";
import { useState, useCallback } from "react";
import { AuthUser } from "@/lib/types";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";
const TOKEN_KEY = "omni_token";

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(() => {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(TOKEN_KEY);
    return raw ? JSON.parse(raw) : null;
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const _request = async (path: string, email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${AI_ENGINE_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Auth failed");
      const authUser: AuthUser = { email: data.email, token: data.token };
      localStorage.setItem(TOKEN_KEY, JSON.stringify(authUser));
      setUser(authUser);
      return authUser;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Auth failed";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const login = useCallback((email: string, password: string) =>
    _request("/auth/login", email, password), []);

  const register = useCallback((email: string, password: string) =>
    _request("/auth/register", email, password), []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  return { user, loading, error, login, register, logout };
}
