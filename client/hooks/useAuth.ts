"use client";
import { useCallback, useEffect } from "react";
import { AuthUser } from "@/lib/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setUser, setLoading, setError, logout as logoutAction } from "@/store/slices/authSlice";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";
const TOKEN_KEY = "omni_token";

export function useAuth() {
  const dispatch = useAppDispatch();
  const { user, loading, error } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (!user) {
      const raw = localStorage.getItem(TOKEN_KEY);
      if (raw) dispatch(setUser(JSON.parse(raw)));
    }
  }, [user, dispatch]);

  const _request = async (path: string, email: string, password: string) => {
    dispatch(setLoading(true));
    dispatch(setError(null));
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
      dispatch(setUser(authUser));
      return authUser;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Auth failed";
      dispatch(setError(msg));
      return null;
    } finally {
      dispatch(setLoading(false));
    }
  };

  const login = useCallback((email: string, password: string) =>
    _request("/auth/login", email, password), [dispatch]);

  const register = useCallback((email: string, password: string) =>
    _request("/auth/register", email, password), [dispatch]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    dispatch(logoutAction());
  }, [dispatch]);

  return { user, loading, error, login, register, logout };
}
